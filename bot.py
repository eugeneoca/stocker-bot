import discord
from discord.ext import commands
from storemanager import *
from discord.utils import get
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class Bot():

    token = ""
    processor = discord.Client()
    bot_created = False
    version = "V1.0.0.0"
    store_manager = StoreManager()
    v_cart = []
    
    def __init__(self, token):
        if token=="":
            print("Your bot cannot find the token.")
        else:
            #self.chrome = webdriver.Chrome()
            self.token = token
            self.bot = commands.Bot(command_prefix="s!")
            self.activate_commands()

    def activate_commands(self):
        @self.bot.event
        async def on_ready():
            print("Stocker is running.")

        @self.bot.event
        async def on_command_error(context, exception):
            embed = discord.Embed(title = "Problem Occured", description = str(exception), color=0xFF0000)
            await context.message.channel.send(embed= embed)

        @self.bot.event
        async def on_message(message):
            message.content.lower()
            #if message.author.id==761726793911762955:
            #    await message.add_reaction('\u23ee')

            if message.author == self.bot.user:
                #print(message.author)
                return

            if message.content.startswith("hello"):
                await message.channel.send("WTF it works!")
            
            await self.bot.process_commands(message)

        @self.bot.command(
            name="version",
            description="Get the current version of Stocker bot.\n Syntax: stocker!version",
            brief="Get Current Version.",
            aliases=["ver", "vsn", "v"],
            pass_context=True
        )
        async def version(context):
            if context.message.author == self.bot.user:
                return

            await context.message.channel.send(f"""`Current version: {self.version}`""")

        @self.bot.command(
            name="store",
            description="Add, Remove, Manage and Monitor stores. \n Syntax: stocker!store <action> <url>",
            brief="Manage Stores.",
            aliases = ['s', 'str'],
            pass_context=True,
        )
        async def store(context, action="", url=""):
            if context.message.author == self.bot.user:
                return

            try:

                if action == "add":
                    result = self.store_manager.register_store(domain_name=url)
                    await context.message.channel.send(result)
                elif action == "list":
                    result = self.store_manager.get_stores()
                    description = "Complete list of registered stores.\n\n"
                    if len(result):
                        for store_id, store_name in result:
                            description += "`"+str(store_id)+"` " + store_name + "\n"
                    else:
                        description += "`No registered store.`\n"

                    description+="\n"
                    embed = discord.Embed(title = "Registered Stores", description = description, color=0x00ff00)
                    embed.set_footer(text="Stocker V1.0.0", icon_url= "https://www.iconfinder.com/icons/4852563/download/png/512")
                    await context.message.channel.send(embed= embed)
                elif action == "remove":
                    result = self.store_manager.unregister_store(url)
                    await context.message.channel.send(result)
                else:
                    await context.message.channel.send("`Invalid command`")
            except Exception as error:
                await context.message.channel.send("`Invalid command`. "+str(error))

        @self.bot.command(
            name="product",
            description="Add, Remove, Manage and Monitor Products.\n Syntax: stocker!product <action> <payload>",
            brief="Manage Products.",
            aliases = ['p', 'pro'],
            pass_context=True,
        )
        async def product(context, action="", payload=""):
            if context.message.author == self.bot.user:
                return

            try:

                if action == "add":
                    result = self.store_manager.register_product(payload)
                    await context.message.channel.send(result)
                elif action == "view":
                    result = self.store_manager.view_product(payload)
                    description = "View Product\n\n"
                    if len(result):
                        for product_id, product_url, status, store_name in result:
                            description += "ID:\t"+str(product_id) +"\n"
                            description += "STORE:\t"+str(store_name) +"\n"
                            description += "URL:\t"+str(product_url) +"\n\n"
                            if int(status)==1:
                                description += "STATUS:\tAvailable\n\n"
                            else:
                                description += "STATUS:\tUnavailable\n\n"
                    else:
                        description += "`Product not found.`\n"

                    description+="\n"
                    embed = discord.Embed(title = "Product", description = description, color=0x00ff00)
                    embed.set_footer(text="Stocker V1.0.0", icon_url= "https://www.iconfinder.com/icons/4852563/download/png/512")
                    sent_message = await context.message.channel.send(embed= embed)
                    await sent_message.add_reaction("🛒")

                    def check_for_reaction(reaction, user):
                        return user == context.message.author and str(reaction.emoji) == '🛒'

                    try:
                        reaction, user = await self.bot.wait_for('reaction_add', timeout=30, check=check_for_reaction)
                    except Exception as error:
                        await context.message.channel.send("Invalid Reaction")
                    else:
                        if status == 1:
                            self.v_cart.append(product_id)
                            await context.message.channel.send("This product is added to cart.")
                        else:
                            await context.message.channel.send("Product unavailable at the moment.")

                elif action == "remove":
                    result = self.store_manager.unregister_product(payload)
                    await context.message.channel.send(result)
                elif action == "list":
                    result = self.store_manager.get_products()
                    description = "Complete list of registered products.\n\n"
                    if len(result):
                        for product_id, product_url, status, store_name in result:
                            description += "ID:\t"+str(product_id) +"\n"
                            description += "STORE:\t"+str(store_name) +"\n"
                            description += "URL:\t"+str(product_url) +"\n\n"
                            if int(status)==1:
                                description += "STATUS:\tAvailable\n\n"
                            else:
                                description += "STATUS:\tUnavailable\n\n"
                    else:
                        description += "`No registered products.`\n"

                    description+="\n"
                    embed = discord.Embed(title = "Registered Products", description = description, color=0x00ff00)
                    embed.set_footer(text="Stocker V1.0.0", icon_url= "https://www.iconfinder.com/icons/4852563/download/png/512")
                    await context.message.channel.send(embed= embed)
                else:
                    await context.message.channel.send("`Invalid command`")
            except Exception as error:
                await context.message.channel.send("`Invalid command`. "+str(error))

        @self.bot.command(
            name="monitor",
            description="Activate/Deactivate Monitoring.\n Syntax: stocker!monitor <action>",
            brief="Monitor Products.",
            aliases = ['m', 'moni'],
            pass_context=True,
        )
        async def monitor(context, action=""):
            if context.message.author == self.bot.user:
                return

            try:

                if action == "activate":
                    result = self.store_manager.activate_monitoring()
                    await context.message.channel.send(result)
                elif action == "deactivate":
                    result = self.store_manager.deactivate_monitoring()
                    await context.message.channel.send(result)
                elif action == "status":
                    result = self.store_manager.get_monitor_status()
                    if result:
                        await context.message.channel.send("`Monitor is up.`")
                    else:
                        await context.message.channel.send("`Monitor is down.`")
                else:
                    await context.message.channel.send("`Invalid command`")
            except Exception as error:
                await context.message.channel.send("`Invalid command`. "+str(error))

        @self.bot.command(
            name="cart",
            description="Cart commands.\n Syntax: stocker!cart <action>",
            brief="Virtual Cart.",
            aliases = ['c'],
            pass_context=True,
        )
        async def cart(context, action=""):
            if context.message.author == self.bot.user:
                return

            try:

                if action == "list":
                    description = "Cart items list.\n\n"
                    if len(self.v_cart):
                        for product_id in self.v_cart:
                            for product_id, product_url, status, store_name in self.store_manager.view_product(product_id):
                                description += "ID:\t"+str(product_id) +"\n"
                                description += "STORE:\t"+str(store_name) +"\n"
                                description += "URL:\t"+str(product_url) +"\n\n"
                                if int(status)==1:
                                    description += "STATUS:\tAvailable\n\n"
                                else:
                                    description += "STATUS:\tUnavailable\n\n"
                    else:
                        description += "`The cart is empty.`\n"

                    description+="\n"
                    embed = discord.Embed(title = "Virtual Cart", description = description, color=0x00ff00)
                    embed.set_footer(text="Stocker V1.0.0", icon_url= "https://www.iconfinder.com/icons/4852563/download/png/512")
                    await context.message.channel.send(embed= embed)
                elif action == "checkout":
                    pass
                    #result = self.store_manager.deactivate_monitoring()
                    #await context.message.channel.send(result)
                else:
                    await context.message.channel.send("`Invalid command`")
            except Exception as error:
                await context.message.channel.send("`Invalid command`. "+str(error))

    def get_token(self):
        return self.token

    def run(self):
        self.bot.run(self.get_token())


