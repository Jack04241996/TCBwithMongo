import os
from pymongo import AsyncMongoClient


MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB", "tcb")

_client: AsyncMongoClient | None = None

async def get_client() -> AsyncMongoClient:
    global _client
    if _client is None:
        _client = AsyncMongoClient(MONGO_URL, serverSelectionTimeoutMS=10000, maxPoolSize=100)
    return _client

async def close_client():
    global _client
    if _client is not None:
        await _client.close()
        _client = None

async def ping():
    client = await get_client()
    await client.admin.command("ping")

async def get_db():
    client = await get_client()
    return client[MONGO_DB]

# ---- Collection providers（給 Depends 用）----
async def users_col():
    return (await get_db())["users"]

async def products_col():
    return (await get_db())["products"]

async def carts_col():
    return (await get_db())["carts"]

async def orders_col():
    return (await get_db())["orders"]

# ---- 索引（冪等；prestart / lifespan 都能叫）----
async def ensure_indexes():
    carts  = await carts_col()
    orders = await orders_col()
    await carts.create_index([("username", 1), ("status", 1)], name="ix_username_status")
    await orders.create_index([("orderNo", 1)], unique=True, name="ux_orderNo")
    await orders.create_index([("account", 1), ("createdAt", -1)], name="ix_account_createdAt_desc")
