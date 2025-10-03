from fastapi import FastAPI, HTTPException , Request , status
from fastapi.responses import JSONResponse , FileResponse , PlainTextResponse
from database import users_collection , products_collection , carts_collection, ensure_cart_indexes , ensure_order_indexes , orders_collection
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from middleware import  require_level, JWTAuthMiddleware
from jwt_handler import create_jwt , decode_jwt
import os
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from passlib.context import CryptContext
from model import RegisterData , LoginData , UserUpdate , CartItem
from contextlib import asynccontextmanager
from datetime import datetime , timezone
from urllib.parse import urlsplit, urlunsplit
from ECpay.ECpay_sdk import ECPayPaymentSdk
import secrets


load_dotenv(override=False) 
SECRET_KEY = os.getenv("SECRET_KEY")
MERCHANT_ID = os.getenv("MERCHANT_ID")
HASH_KEY    = os.getenv("HASH_KEY")
HASH_IV     = os.getenv("HASH_IV")
ECPAY_STAGE = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL")
BASE_URL = os.getenv("BASE_URL")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
sdk = ECPayPaymentSdk(MerchantID=MERCHANT_ID, HashKey=HASH_KEY, HashIV=HASH_IV)
 #test3

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
    uri = os.getenv("MONGO_URI", "")
    print("▶ Using MONGO_URI:", _redact(uri))
    app.state.mongo = None
    app.state.db = None
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=10000, maxPoolSize=100)
        client.admin.command("ping")
        app.state.mongo = client
        app.state.db = client[os.getenv("DB_NAME", "tcb")]
        print("✅ Mongo ready")
        await ensure_cart_indexes()
        print("✅ Cart indexes ready")
        await ensure_order_indexes()
        print("✅ Order indexes ready")
    except PyMongoError as e:
        print("❌ Mongo not ready:", e)
    try:
        yield
    finally:
        if app.state.mongo:
            app.state.mongo.close()
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
    payload = { "account": user["account"],"username": user["username"], "level": int(user["level"])}
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
# -----------------購物車-----------------------------

def _totals(items: list[dict]):
    subtotal = sum(int(i.get("price", 0)) * int(i.get("quantity", 0)) for i in items)
    count = sum(int(i.get("quantity", 0)) for i in items)
    return {"subtotal": subtotal, "count": count}

def _require_login(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")
    return user

def gen_order_no() -> str:
    return datetime.now(timezone.utc).strftime("ODR%Y%m%d") + secrets.token_hex(4).upper()


@app.get("/cart")
async def get_cart(request: Request):
    return FileResponse("static/Product/cart.html")

# 取得購物車（前端用這個拉資料）
@app.get("/api/cart")
async def get_cart(request: Request):
    user = _require_login(request)
    account = user["account"]             # ← 只信 JWT
    cart = await carts_collection.find_one({"account": account, "status": "active"}, {"_id": 0})
    items = cart.get("items", []) if cart else []
    return {"cart": items, "total": _totals(items)}

# 加入/累加購物車
@app.post("/api/cart")
async def add_to_cart(request: Request):
    user = _require_login(request)
    account = user["account"]

    data = await request.json()
    name = (data.get("name") or "").strip()
    quantity = int(data.get("quantity") or 0)
    if not name or quantity <= 0:
        return JSONResponse(status_code=400, content={"error": "name/quantity 不合法"})

    product = await products_collection.find_one({"name": name}, {"_id": 0})
    if not product:
        return JSONResponse(status_code=404, content={"error": "商品不存在"})
    price = int(product.get("price", 0))

    cart = await carts_collection.find_one({"account": account, "status": "active"}, {"_id": 0})
    items = cart.get("items", []) if cart else []

    for it in items:
        if it["name"] == name:
            it["quantity"] = int(it.get("quantity", 0)) + quantity
            it["price"] = price
            break
    else:
        items.append({
            "name": name,
            "quantity": quantity,
            "price": price,
            "img": product.get("img"),
            
        })

    await carts_collection.update_one(
        {"account": account, "status": "active"},
        {"$set": {"items": items,
                  "account": account, "status": "active"}},  # 首次 upsert 也會帶入
        upsert=True,
    )
    return JSONResponse(status_code=201, content={"success": True, "cart": items, "total": _totals(items)})

# 移除單一項目
@app.delete("/api/cart/items/{name}")
async def remove_from_cart(request: Request, name: str):
    # 只信 JWT 拿 account
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Unauthorized")
    account = user["account"]

    filter_ = {"account": account, "status": "active"}

    # 用 $pull 把 items 陣列裡 name=指定值 的項目移除；同時更新 updatedAt
    result = await carts_collection.update_one(
        filter_,
        {"$pull": {"items": {"name": name}}}
    )

    if result.modified_count == 0:
        # 沒有那個項目（或購物車不存在）
        return JSONResponse(status_code=404, content={"error": "項目不存在或購物車不存在"})

    # 兩種回應擇一：A) 回傳最新購物車；B) 回 204 讓前端自行重抓
    cart = await carts_collection.find_one(filter_, {"_id": 0, "items": 1})
    return JSONResponse({"success": True, "cart": cart["items"], "total": _totals(cart["items"])})

@app.patch("/api/cart/items/{name}")
async def set_quantity(request: Request, name: str, body: dict):
    user = _require_login(request)
    qty = int(body.get("quantity", -1))
    if qty < 0:
        raise HTTPException(400, "quantity 需為非負整數")
    # qty==0 建議改用 DELETE /api/cart/items/{name}
    result = await carts_collection.update_one(
        {"account": user["account"], "status": "active", "items.name": name},
        {"$set": {"items.$.quantity": qty}}
    )
    if result.matched_count == 0:
        raise HTTPException(404, "項目不存在")
    cart = await carts_collection.find_one({"account": user["account"], "status": "active"}, {"_id": 0, "items": 1})
    return {"cart": cart["items"], "total": _totals(cart["items"])}

# 清空購物車
@app.delete("/api/cart")
async def clear_cart(request: Request):
    user = _require_login(request)
    account = user["account"]  # 一律信 JWT

    filter_ = {"account": account, "status": "active"}
    await carts_collection.update_one(
        filter_,
        {"$set": {"items": []}},
        upsert=False,  # 通常清空不需要幫你建立新車；想自動建立就改 True 並同時 $setOnInsert account/status
    )

    # 策略 A：永遠回空車（前端簡單）
    return {"success": True, "cart": [], "total": {"subtotal": 0, "count": 0}}

@app.post("/api/checkout")
async def create_checkout_session(request: Request):
    user = _require_login(request)
    account = user["account"]
    cart = await carts_collection.find_one({"account": account, "status": "active"}, {"_id": 0})
    items = (cart or {}).get("items") or []

    if not items:
        raise HTTPException(status_code=400, detail="購物車為空")
    
    total = _totals(items)  # 可能回 dict 或 int，看你的實作

    amount = int(total["subtotal"]) if isinstance(total, dict) else int(total)

    if amount <= 0:
        raise HTTPException(status_code=400, detail="金額錯誤")

    # 2) 建立訂單（省略：寫入 DB，狀態 PENDING）
    order_id = gen_order_no()

    upd = {
        "status": "pending",
        "merchant_trade_no": order_id,
        "amount_snapshot": amount,
        "items_snapshot": items,
        "provider": "ECPay",
        "paid_at": None,
        "attempt": int((cart or {}).get("attempt", 0)) + 1,
        "updated_at": datetime.now(timezone.utc),
    }
    await carts_collection.update_one(
        {"account": account, "status": "active"},
        {"$set": upd},
        upsert=False
    )
    # 3) 組 ECPay 欄位（ChoosePayment=ALL）
    params = {
        "MerchantTradeNo": order_id,
        "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "PaymentType": "aio",
        "TotalAmount": amount,
        "TradeDesc": "TEST ORDER",
        "ItemName": "#".join(i.get("name","") for i in items) or "訂單",
        "ChoosePayment": "ALL",
        "ReturnURL": f"{BASE_URL}/payment/notify",         # Webhook（要公網）
        "OrderResultURL": f"{BASE_URL}/payment/return",  # 導回頁（可本機）
        "ClientBackURL": f"{FRONTEND_BASE_URL}/",
        "NeedExtraPaidInfo": "Y",
        "EncryptType": 1,
    }

    fields = sdk.create_order(params)
    return JSONResponse({"action": ECPAY_STAGE, "method": "POST", "fields": fields})

import logging
logger = logging.getLogger("ecpay")
logger.setLevel(logging.INFO)

@app.post("/payment/notify", response_class=PlainTextResponse)
async def ecpay_notify(request: Request):
    form = dict((await request.form()).items())

    merchant_trade_no = form.get("MerchantTradeNo")
    rtn_code = str(form.get("RtnCode", ""))
    logger.info("[ECPAY] notify arrive no=%s rtn=%s", merchant_trade_no, rtn_code)

    # 1) 驗簽（HTTP 200；內容決定是否重送）
    try:
        if not sdk.verify_notify_mac(form):
            # 已在 verify_notify_mac 印 given/calc；再補 payload 方便對照
            logger.error("[ECPAY] BAD_MAC no=%s payload=%s", merchant_trade_no, form)
            return PlainTextResponse("0|FAIL")
    except Exception as e:
        logger.exception("[ECPAY] MAC_EXCEPTION no=%s err=%s payload=%s", merchant_trade_no, e, form)
        return PlainTextResponse("0|FAIL")

    # 2) 解析金額（回呼比對只看 TradeAmt；測試若有 amount 也不作為主要依據）
    try:
        trade_amt = int(form.get("TradeAmt", "0"))
    except Exception:
        logger.warning("[ECPAY] BAD_TRADE_AMT no=%s raw=%s", merchant_trade_no, form.get("TradeAmt"))
        return PlainTextResponse("0|FAIL")

    # 3) 找單（冪等：找不到視為已處理）
    cart = await carts_collection.find_one({"merchant_trade_no": merchant_trade_no})
    if not cart:
        logger.warning("[ECPAY] CART_NOT_FOUND no=%s", merchant_trade_no)
        return PlainTextResponse("1|OK")

    # 4) 若非 pending（可能已被其它通知/流程更新）
    status_now = cart.get("status")
    if status_now != "pending":
        logger.info("[ECPAY] NON_PENDING no=%s status=%s -> idempotent OK", merchant_trade_no, status_now)
        return PlainTextResponse("1|OK")

    # 5) 金額比對（用建立訂單時存的快照）
    try:
        expect_amt = int(cart.get("amount_snapshot", -1))
    except Exception:
        expect_amt = -1
    if expect_amt != trade_amt:
        logger.warning("[ECPAY] AMOUNT_MISMATCH no=%s expect=%s got=%s", merchant_trade_no, expect_amt, trade_amt)
        return PlainTextResponse("0|FAIL")

    # 6) 準備更新（成功→success；未成功→active 讓使用者回購物車再試）
    now = datetime.now(timezone.utc)
    updates = {
        "provider_payload": form,
        "updated_at": now,
    }
    if rtn_code == "1":  # 成功
        updates.update({
            "status": "success",
            "provider_trade_no": form.get("TradeNo"),
            "paid_at": now,
        })
    else:  # 未成功 → active（保留購物車內容）
        updates.update({
            "status": "active",
            "provider_trade_no": None,
            "paid_at": None,
            "last_payment_failed": True,
            "failure_reason": form.get("RtnMsg") or "PaymentNotSuccessful",
        })

    res = await carts_collection.update_one(
        {"merchant_trade_no": merchant_trade_no, "status": "pending"},
        {"$set": updates}
    )
    logger.info("[ECPAY] UPDATE no=%s matched=%s modified=%s -> %s",
                merchant_trade_no, res.matched_count, res.modified_count, updates["status"])

    # 7) 所有處理完成 → **一定回純文字 1|OK**
    return PlainTextResponse("1|OK")


@app.api_route("/payment/return", methods=["POST"])
async def payment_return(request: Request):
    return FileResponse("static/home.html")

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)