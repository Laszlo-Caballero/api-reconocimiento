from decorator.singleton import singleton
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from pgvector.sqlalchemy import Vector

@singleton
class PostgreDatabase:
    def __init__(self):
        print("Initializing PostgreDatabase connection pool...")
        
        database_url = f"postgresql+psycopg2://{os.getenv('DATABASE_USER')}:{os.getenv('DATABASE_PASSWORD')}@{os.getenv('DATABASE_HOST')}:{os.getenv('DATABASE_PORT')}/{os.getenv('DATABASE_NAME')}"
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self) -> Session:
        return self.SessionLocal()
    
    def close(self):
        self.engine.dispose()