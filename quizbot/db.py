import os
from pymongo import MongoClient

client = MongoClient(os.environ['MONGO_HOST'])
db = client['quiz_posts']
