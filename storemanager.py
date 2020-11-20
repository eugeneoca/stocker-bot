from selectorlib import Extractor
import requests 
import json 
from time import sleep
from database import *
from threading import Thread
from urllib.parse import urlparse
from urllib.request import urlopen,Request
import json
from discord_notify import Notifier
import discord
from discord import Webhook, RequestsWebhookAdapter
from discord.ext import commands

class StoreManager:
    db = ""
    monitoring_enabled = False

    #webhook_embedded = Webhook.from_url("https://discordapp.com/api/webhooks/764782627282354206/9iGrCAxDsHz-WfV0Bhj0A2QoxqD8u0_w91rCHYSwRap87uDMgGv4Ud9jYxXI04gqQTCm", adapter=RequestsWebhookAdapter()) # For client
    webhook_embedded = Webhook.from_url("https://discord.com/api/webhooks/761726793911762955/f5mM1eXD8yrX9VmCQguBJlrRIxev7Bp6ivYWs_oSalS-OR9kKeZWiEIQOZGf5NhkR53R", adapter=RequestsWebhookAdapter())

    def __init__(self):
        self.db = Database(
            host="localhost",
            user="root",
            password="",
            db_name="stocker"
        )
        _p = Thread(target=self.monitor, name="Monitor")
        _p.daemon = True
        _p.start()

    def register_store(self, domain_name):
        domain_name = self.normalize_url(domain_name)
        try:
            with self.db.get_cursor() as cursor:
                query = "INSERT INTO stores (domain) VALUES (%s)"
                values = [(domain_name)]
                cursor.execute(query, values)
                self.db.db_instance.commit()
                return "`Store registration successful.`"
        except Exception as error:
            return "`Problem registering name. "+str(error)+"`"

    def normalize_url(self, url):
        if not (url.startswith('//') or url.startswith('http://') or url.startswith('https://')):
            url = '//' + url
        return urlparse(url).netloc

    def get_stores(self):
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM stores")
            return cursor.fetchall()

    def unregister_store(self, store_id):
        try:
            with self.db.get_cursor() as cursor:
                query = "DELETE FROM stores WHERE id = '"+store_id+"'"
                cursor.execute(query)
                self.db.db_instance.commit()
                return "`Store has been removed.`"
        except Exception as error:
            return "`Problem removing a store. "+str(error)+"`"

    def resolve_url(self, url):
        header = { 'User-Agent' : 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)' }
        req = Request(url, headers=header)
        return urlopen(req).geturl()

    def register_product(self, url):
        try:
            domain = self.normalize_url(url)
            store_id = 0
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM stores WHERE domain = '"+str(domain)+"' LIMIT 1")
                result = cursor.fetchall()
                if len(result):
                    store_id, _ = result[0]
                else:
                    return "`Not from a registered store.`"
            url = self.resolve_url(url)
            with self.db.get_cursor() as cursor:
                query = "INSERT INTO products (product_url, store_id) VALUES (%s,%s)"
                values = (url, store_id)
                cursor.execute(query, values)
                self.db.db_instance.commit()
                cursor.close()
                return "`Product registration successful.`"
        except Exception as error:
            return "`Problem adding a product. "+str(error)+"`"

    def view_product(self, product_id):
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT t1.id, product_url, instock, domain FROM products t1 LEFT JOIN stores t2 ON t1.store_id = t2.id WHERE t1.id = '"+str(product_id)+"' ORDER BY domain LIMIT 1")
            result = cursor.fetchall()
            return result

    def unregister_product(self, product_id):
        try:
            with self.db.get_cursor() as cursor:
                query = "DELETE FROM products WHERE id = '"+product_id+"'"
                cursor.execute(query)
                self.db.db_instance.commit()
                cursor.close()
                return "`Product has been removed.`"
        except Exception as error:
            return "`Problem removing a product. "+str(error)+"`"

    def get_products(self):
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT t1.id, product_url, instock, domain FROM products t1 LEFT JOIN stores t2 ON t1.store_id = t2.id ORDER BY domain")
            return cursor.fetchall()

    def activate_monitoring(self):
        try:
            self.monitoring_enabled = True
            return "`Monitor activated.`"
        except Exception as error:
            return "`Activation failed. "+str(error)+"`"

    def deactivate_monitoring(self):
        try:
            self.monitoring_enabled = False
            return "`Monitor deactivated.`"
        except Exception as error:
            return "`Deactivation failed. "+str(error)+"`"
    
    def get_monitor_status(self):
        return self.monitoring_enabled

    def monitor(self):
        while True:
            try:
                if self.monitoring_enabled:
                    for product_id, product_url, instock, domain in self.get_products():
                        source = self.scrape(product_url, 'selectors/amazon_availability.yml')
                        if source['availability'] != None:

                            # Notify when product becomes available
                            try:
                                if "unavailable" not in source['availability']:
                                    if int(instock) == 0:
                                        with self.db.get_cursor() as cursor:
                                            cursor.execute("UPDATE products SET instock = '1' WHERE id = '"+str(product_id)+"'")
                                            self.db.db_instance.commit()
                                            #self.webhook_client.send("`"+ str(product_url) +" is now available!`") # Notify only

                                            embed = discord.Embed(title = "Product Available", description = product_url, url=product_url,color=0x00ff00)
                                            embed.set_footer(text="Stocker V1.0.0", icon_url= "https://www.iconfinder.com/icons/4852563/download/png/512")
                                            self.webhook_embedded.send(embed=embed)
                                            cursor.close()
                            except Exception as error:
                                if int(instock)>0:
                                    with self.db.get_cursor() as cursor:
                                        cursor.execute("UPDATE products SET instock = '0' WHERE id = '"+str(product_id)+"'")
                                        self.db.db_instance.commit()
                                        #self.webhook_client.send("`"+ str(product_url) +" is now unavailable!`") Notify Only

                                        embed = discord.Embed(title = "Product Unvailable", description = product_url, url=product_url,color=0x00ff00)
                                        embed.set_footer(text="Stocker V1.0.0", icon_url= "https://www.iconfinder.com/icons/4852563/download/png/512")
                                        
                                        self.webhook_embedded.send(embed=embed)
                                        cursor.close()

                                
                        """else:
                            # Notify on product out of stock
                            if int(instock)>0:
                                with self.db.get_cursor() as cursor:
                                    cursor.execute("UPDATE products SET instock = '0' WHERE id = '"+str(product_id)+"'")
                                    self.db.db_instance.commit()
                                    self.webhook.send("`"+ str(product_url) +" is now unavailable!`")
                                    cursor.close()"""
                else:
                    sleep(2)
            except Exception as error:
                print("Unexpected error on monitor. "+str(error))

    def scrape(self, url, selector):    
        e = Extractor.from_yaml_file(selector)
        headers = {
            'authority': 'www.amazon.com',
            'pragma': 'no-cache',
            'cache-control': 'no-cache',
            'dnt': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; CrOS x86_64 8172.45.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.64 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-dest': 'document',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }
        r = requests.get(url, headers=headers)
        if r.status_code > 500:
            print("Access denied on "+str(url))
            return None
        return e.extract(r.text)
        