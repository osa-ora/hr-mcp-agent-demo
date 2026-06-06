from sqlalchemy import create_engine
from config import DATABASE_URL

# Make sure to create the DB using:
# DROP DATABASE hrdb;
# CREATE DATABASE hrdb;

#print("DATABASE_URL =", DATABASE_URL)

engine = create_engine(
    DATABASE_URL or "postgresql+psycopg2://postgres:postgres@localhost:5432/hrdb",
    echo=False
)