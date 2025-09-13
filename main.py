from fastapi import FastAPI, HTTPException , Request
from fastapi.responses import  RedirectResponse ,JSONResponse , FileResponse
from database import users_collection , products_collection , client, db_user
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from middleware import  require_level, JWTAuthMiddleware
from jwt_handler import create_jwt , decode_jwt
import os
from passlib.context import CryptContext
from model import RegisterData , LoginData , UserUpdate, CartItem
from contextlib import asynccontextmanager
from urllib.parse import urlsplit, urlunsplit

load_dotenv() 
SECRET_KEY = os.getenv("SECRET_KEY")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

 #test2
def _redact(uri: str) -> str:
    if not uri:
        return ""
    p = urlsplit(uri)
    netloc = p.netloc
    # 隱藏密碼
    if "@" in netloc and ":" in netloc.split("@", 1)[0]:
        user, host = netloc.split("@", 1)
        user = user.split(":")[0] + ":****"
        netloc = user + "@" + host
    return urlunsplit((p.scheme, netloc, p.path, p.query, p.fragment))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---- startup 區塊 ----
    print("▶ Using MONGO_URI:", _redact(os.getenv("MONGO_URI", "")))
    try:
        await client.admin.command("hello")  # 確認能連
        n = await db_user["products"].count_documents({})
        print(f"✅ Mongo OK，products 筆數 = {n}")
    except Exception as e:
        print("❌ Mongo 連線失敗：", e)
        raise  # 啟動失敗時直接中止

    yield  # ---- app 服務運行中 ----

    # ---- shutdown 區塊 ----
    await client.aclose()
    print("🛑 Mongo client closed.")

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/image", StaticFiles(directory="image"), name="image")
app.add_middleware(JWTAuthMiddleware)

@app.get("/health", include_in_schema=False)
async def health():
    return {"ok": True}


@app.get("/")
async def serve_home_page():
    return FileResponse("static/home.html")

#-----------------------------Login-------------------------------------------#
@app.get("/login")
async def get_login_page():
    return FileResponse("static/User/login.html")

@app.post("/api/login")
async def login(data: LoginData):
    user = await users_collection.find_one({"account": data.account})
    if not user or not pwd_context.verify(data.password, user["password"]):
        return JSONResponse(status_code=400, content={"error": "帳號密碼錯誤"})
    payload = {"username": user["username"], "level": int(user["level"])}
    token = create_jwt(payload, expires_in=10)
    return JSONResponse(content={"message": "登入成功", "token": token})


@app.get("/api/user")
async def get_user(request: Request):
    token = request.headers.get("Authorization")

    if not token or not token.startswith("Bearer "):
        return JSONResponse(content={"username": None})

    token = token.replace("Bearer ", "")
    user_data = decode_jwt(token)

    if user_data is None:
        return JSONResponse(content={"username": None})

    return JSONResponse(content={
        "username": user_data["username"],
        "level": user_data["level"]
    })



#------------------------------註冊-------------------------------------------#
@app.get("/build")
async def get_build_page(request: Request):
    return FileResponse("static/User/build.html")

@app.post("/api/register")
async def register_user(request: Request, body: RegisterData ):


    if await users_collection.find_one({"email": body.email}):
        return JSONResponse(
            status_code=400,
            content={"error": "Email已存在，請重新輸入"}
        )

    if await users_collection.find_one({"account": body.account}):
        return JSONResponse(
            status_code=400,
            content={"error": "帳號已存在，請重新輸入"}
        )

    if await users_collection.find_one({"phone": body.phone}):
        return JSONResponse(
            status_code=400,
            content={"error": "電話已存在，請重新輸入"}
        )
    
    hashed_password = pwd_context.hash(body.password)

    await users_collection.insert_one({
        "account": body.account,
        "password": hashed_password,
        "username": body.username,
        "phone": body.phone,
        "email": body.email,
        "level": "0"
    })

    return JSONResponse(status_code=201, content={"message": "註冊成功"})

    
#------------------------使用者管理------------------------#
# 使用者列表
@app.get("/users_management")
async def serve_users_page():
    return FileResponse("static/User/users_management.html")

@app.get("/api/users_management")
@require_level([2,3])
async def user_list(request: Request):
    users = await users_collection.find({}, {"_id": 0}).to_list(length=None)
    return JSONResponse(content= {    
        "users": users         
    })

# 刪除使用者
@app.delete("/api/user_delete/{account}")
@require_level([2,3])
async def delete_user(request: Request, account: str):
    users = await users_collection.delete_one({"account": account})
    if users.deleted_count == 1:
        return JSONResponse(status_code=200, content={"message": "刪除成功"})
    
@app.get("/user_edit/{account}")
async def serve_users_edit_page(request: Request, account: str):
    return FileResponse("static/User/user_edit.html")

# 編輯頁面
@app.get("/api/user_edit/{account}")
@require_level([2,3])
async def edit_user(request: Request, account: str):
    user = await users_collection.find_one({"account": account}, {"_id": 0})
    return JSONResponse(content={
        "user": user
    })

# 更新使用者
@app.patch("/api/user_edit/{account}")
@require_level([2,3])
async def update_user(request: Request, account: str, body: UserUpdate):
    update_fields = {
        "username": body.username,
        "phone": body.phone,
        "email": body.email,
    }

    if body.level is not None:
        current_user = getattr(request.state, "user", None)
        if not current_user or int(current_user.get("level", 0)) < 3:
            raise HTTPException(status_code=403, detail="Not allowed to change level")
        update_fields["level"] = int(body.level)

    # 去掉 None 的欄位，避免把欄位設成 null
    update_fields = {k: v for k, v in update_fields.items() if v is not None}

    await users_collection.update_one({"account": account}, {"$set": update_fields})
    return JSONResponse(status_code=200, content={"message": "編輯成功"})

# ----------------品牌故事頁-------------------------------
@app.get("/story")
async def story():
    return FileResponse("static/story.html")
#------------------產品頁面-----------------------------
@app.get("/products")
async def serve_product_page():
    return FileResponse("static/Product/products.html")

@app.get("/api/products")
async def get_product_page(request: Request):
    cursor = products_collection.find({}, {"_id": 0})
    products = await cursor.to_list(length=None)

    return JSONResponse(content={
        "products": products
    })
#
# @app.post("/add_to_cart")
# async def add_to_cart(item: CartItem, request: Request):
#     cart = request.session.get("cart", [])

#     # 已存在就加數量
#     for it in cart:
#         if it["name"] == item.name:
#             it["quantity"] += item.quantity
#             break
#     else:
#         cart.append(item.model_dump())

#     request.session["cart"] = cart
#     return JSONResponse({"success": True})

#------------------產品管理-----------------------------
@app.get("/products_management")
async def serve_product_management_page():
    return FileResponse("static/Product/products_management.html")

@app.get("/api/products_management")
@require_level([2,3])
async def get_product_management_page(request: Request):
    products = await products_collection.find({}, {"_id": 0}).to_list(length=None)
    return JSONResponse(content={
        "products": products
    })


@app.delete("/api/products_delete/{name}")
@require_level([2,3])
async def delete_product(request: Request, name: str):
    products = await products_collection.delete_one({"name": name})
    if products.deleted_count == 1:
        return JSONResponse(status_code=200, content={"message": "刪除成功"})
    
@app.get("/products_edit/{name}")
async def serve_product_edit_page(request: Request, name: str):
    return FileResponse("static/Product/products_edit.html")

@app.get("/api/products_edit/{name}")
@require_level([2,3])
async def edit_product(request: Request, name: str):
    products = await products_collection.find_one({"name": name}, {"_id": 0})
    return JSONResponse(content={
        "products": products
    })

@app.patch("/api/products_edit/{name}")
@require_level([2,3])
async def update_product(request: Request, name: str):
    data = await request.json()
    update_fields = {
        "price": data.get("price"),
        "description": data.get("description"),
        "img": data.get("img")
    }
    await products_collection.update_one({"name": name}, {"$set": update_fields})

    return JSONResponse(status_code=200, content={"message": "編輯成功"})


@app.get("/products_build")
async def serve_product_build_page(request: Request):
    return FileResponse("static/Product/products_build.html")   

@app.post("/api/products_build")
@require_level([2,3])
async def register_product(request: Request):
    data = await request.json()  # 從 fetch 傳進來的 JSON 拿資料

    name = data.get("name", "").strip()
    price_str = data.get("price", "").strip()
    try:
        price = int(price_str)
    except ValueError:
        return JSONResponse(status_code=400, content={"error": "價格需為整數"})
    
    img = data.get("img", "").strip()
    description = data.get("description", "").strip()

    if not all([name, price, img, description]):
        return JSONResponse(
            status_code=400,
            content={"error": "所有欄位皆為必填，請勿留空或只填空白"}
        )

    if await products_collection.find_one({"name": name}):
        return JSONResponse(
            status_code=400,
            content={"error": "商品名稱已存在，請重新輸入"}
        )

    await products_collection.insert_one({
        "name": name,
        "price": price,
        "img": img,
        "description": description
    })

    return JSONResponse(status_code=200, content={"message": "新增成功"})

#-----------------購物車-----------------------------
@app.get("/cart")
def view_cart(request: Request):
     return FileResponse("static/Product/cart.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)