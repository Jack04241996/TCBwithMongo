from pymongo import AsyncMongoClient
import os
from datetime import datetime, timezone


MONGO_URI = os.getenv("MONGO_URI") # , "mongodb://host.docker.internal:27017"
client = AsyncMongoClient(MONGO_URI)  # 改成你的 Mongo 位址
db_user = client["TCB"]  # 資料庫名稱
users_collection = db_user["users"]
products_collection = db_user["products"]
carts_collection = db_user["carts"]
orders_collection = db_user["orders"]

async def ensure_cart_indexes():
    await carts_collection.create_index([("username", 1), ("status", 1)])

async def ensure_order_indexes():
    await orders_collection.create_index([("orderNo", 1)], unique=True)
    await orders_collection.create_index([("account", 1), ("createdAt", -1)])
# lifespan 連線成功後：await ensure_order_indexes()

