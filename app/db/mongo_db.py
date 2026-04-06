import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

DEFAULT_MONGO_DATABASE_NAME = "recipe_project"
DEFAULT_RAW_RECIPE_COLLECTION_NAME = "recipes"


def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI")
    return MongoClient(mongo_uri)


def get_mongo_database():
    return get_mongo_client()[DEFAULT_MONGO_DATABASE_NAME]


def get_recipes_collection():
    return get_mongo_database()[DEFAULT_RAW_RECIPE_COLLECTION_NAME]


def get_mongo_database_info():
    mongo_database = get_mongo_database()
    return {
        "database_name": mongo_database.name,
        "collection_names": mongo_database.list_collection_names(),
    }
