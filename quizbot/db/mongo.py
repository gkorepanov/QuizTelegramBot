import os
from pymongo import MongoClient
from pymongo.collection import Collection

client = MongoClient(os.environ['MONGO_HOST'])
db = client['quiz_posts']


def get_collection(name) -> Collection:
    return db[name]

