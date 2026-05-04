from decorator.singleton import singleton
from psycopg2.extensions import connection, cursor
import psycopg2
import os

@singleton
class PostgreDatabase:
    
    connection_db: connection
    cursor_db: cursor
    
    def __init__(self):
        print("Initializing PostgreDatabase connection pool...")
        
        self.connection_db = psycopg2.connect(
            dbname=os.getenv("DATABASE_NAME"),
            user=os.getenv("DATABASE_USER"),
            password=os.getenv("DATABASE_PASSWORD"),
            host=os.getenv("DATABASE_HOST"),
            port=os.getenv("DATABASE_PORT")
        )
        
        self.cursor_db = self.connection_db.cursor()
    
    def execute_query(self, query: str, params: tuple = ()):
        self.cursor_db.execute(query, params)
        self.connection_db.commit()