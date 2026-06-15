import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Set up your PostgreSQL URI in a .env file
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:9699@localhost:5432/social_media_api")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency Injection for DB Sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()