import os
from pymongo import MongoClient

client = MongoClient(os.environ['MONGO_HOST'], int(os.environ['MONGO_PORT']))
db = client['quiz_posts']
