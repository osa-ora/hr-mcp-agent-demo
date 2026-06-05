from sqlalchemy import create_engine

# here you can point to your DB: IP, Port, DB Name, and could be also user/pass
# Make sure to create the DB using:
# DROP DATABASE hrdb;
# CREATE DATABASE hrdb;

engine = create_engine(
    "postgresql+psycopg2://postgres:postgres@localhost:5432/hrdb",
    echo=False
)