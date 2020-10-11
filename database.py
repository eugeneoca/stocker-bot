import mysql.connector as database

class Database():

    db_instance = ""
    db_name = ""

    def __init__(self, host, user, password, db_name):
        self.db_name = db_name
        self.db_instance = database.connect(
            host=host,
            user=user,
            password=password,
            database=db_name
        )

    def get_cursor(self):
        return self.db_instance.cursor()

    def get_db_name(self):
        return self.db_name