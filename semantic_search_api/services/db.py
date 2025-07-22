from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DB_CNN_URL = os.getenv("NEWS_DB_URL")

engine = create_engine(DB_CNN_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)