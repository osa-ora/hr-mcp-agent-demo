from db import engine
from schema import metadata

metadata.create_all(engine)

print("Tables created")