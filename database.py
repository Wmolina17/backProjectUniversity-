import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://wdev6666:dkebsfH5zWHWunQv@dbthinkverse.17ie2.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "mi_app_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

collections = ["Users", "Questions", "Forums", "Resources"]

for collection in collections:
    if collection not in db.list_collection_names():
        db.create_collection(collection)

print("✅ Base de datos conectada y colecciones verificadas.")
