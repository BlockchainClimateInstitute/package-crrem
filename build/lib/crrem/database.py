import psycopg2 as pg
import pandas as pd

class DataQ():

    def __init__(self, query,
                 db="postgres", server="golden-source-2020.cyozpdhauzu4.us-east-2.rds.amazonaws.com",
                 user="postgres", pwd="Bcidatabase2020"):
        self.query      = query
        self.db         = db
        self.server     = server
        self.user       = user
        self.pwd        = pwd
        self.conn       = self.db_connect()
        self.data       = pd.read_sql(self.query, self.conn)
        self.describe   = self.data.describe()
        self.head       = self.data.head(10)
        self.db_disconnect()

    def db_connect(self):
        # add try/except
        conn = None
        try:
            conn = pg.connect(
                host=self.server,
                database=self.db,
                user=self.user,
                password=self.pwd)
        except Exception as err:
            print(err)
        return conn

    def db_disconnect(self):
        self.conn.close()
        pass