from typing import Optional, List, Dict, Any
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

# READ USER
async def get_user_by_account(users, account: str) -> Optional[dict]:
    return await users.find_one({"account": account})

# CREATE
async def user_exists(users, filter_dict: dict) -> bool:
    return await users.find_one(filter_dict) is not None

async def create_user(users, *, account: str, username: str, password: str,
                      phone: str, email: str, level: int = 0) -> dict:
    doc = {
        "account": account,
        "username": username,
        "password": _pwd.hash(password), 
        "phone": phone,
        "email": email,
        "level": level,
    }
    await users.insert_one(doc)
    return {"account": account, "username": username, "phone": phone, "email": email, "level": level}

#Delete user
async def delete_user_by_account(users, account: str) -> bool:
    result = await users.delete_one({"account": account})
    return result.deleted_count == 1

# UPDATE USer
async def update_user_by_account(users, account: str, update_fields: dict) -> bool:
    if not update_fields:
        return False
    result = await users.update_one({"account": account}, {"$set": update_fields})
    return result.matched_count == 1

# READ products

async def get_all_products(products_collection) -> List[Dict[str, Any]]:
    cursor = products_collection.find({}, {"_id": 0})
    products = await cursor.to_list(length=None)
    return products

async def get_product_by_name(products_collection, name: str):
    return await products_collection.find_one({"name": name}, {"_id": 0})

async def create_product(
    products_collection,
    *,
    name: str,
    price: int,
    img: str,
    description: str,
) -> Dict[str, Any]:
    doc = {
        "name": name,
        "price": price,
        "img": img,
        "description": description,
    }
    await products_collection.insert_one(doc)
    return doc


async def product_name_exists(products_collection, name: str) -> bool:
    return await products_collection.find_one({"name": name}) is not None

async def delete_product_by_name(products_collection, name: str) -> bool:
    result = await products_collection.delete_one({"name": name})
    return result.deleted_count == 1


async def update_product(
    products_collection,
    name: str,
    update_fields: dict,
) -> None:

    if not update_fields:
        return
    await products_collection.update_one(
        {"name": name},
        {"$set": update_fields},
    )