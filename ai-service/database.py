import os
from dotenv import load_dotenv  # Add this import
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# Tell Python to load the variables from your .env file
load_dotenv() 

# Now this will grab your Neon URL instead of the localhost fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/dbname")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the SQL Table Structure
class BookCache(Base):
    __tablename__ = "book_caches"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String, index=True)
    grade = Column(String)
    chapter = Column(String)
    gemini_file_id = Column(String, unique=True)
    gemini_cache_id = Column(String, unique=True)

# Create the tables in the database
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()