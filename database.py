from pymongo import AsyncMongoClient
import os

MONGO_URI = os.getenv("MONGO_URI") # , "mongodb://host.docker.internal:27017"
client = AsyncMongoClient(MONGO_URI)  # 改成你的 Mongo 位址
db_user = client["TCB"]  # 資料庫名稱
users_collection = db_user["users"]
products_collection = db_user["products"]

