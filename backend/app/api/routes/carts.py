from app.models import AddToCartRequest, SetQuantityRequest
from fastapi import APIRouter, Depends , HTTPException , status , Request
from fastapi.responses import FileResponse , PlainTextResponse
from datetime import datetime , timezone
import secrets
from dotenv import load_dotenv
from app.api.deps import get_current_user
from app.core.db import carts_col, products_col
from app.core.ECpay.ECpay_sdk import ECPayPaymentSdk
import logging
import os
from app.core.paths import STATIC_DIR

router = APIRouter(tags=["carts"])

logger = logging.getLogger("ecpay")
logger.setLevel(logging.INFO)
load_dotenv(override=False) 
MERCHANT_ID = os.getenv("MERCHANT_ID")
HASH_KEY    = os.getenv("HASH_KEY")
HASH_IV     = os.getenv("HASH_IV")
sdk = ECPayPaymentSdk(MerchantID=MERCHANT_ID, HashKey=HASH_KEY, HashIV=HASH_IV)
ECPAY_STAGE = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL")
BASE_URL = os.getenv("BASE_URL")


def _totals(items: list[dict]):
    subtotal = sum(int(i.get("price", 0)) * int(i.get("quantity", 0)) for i in items)
    count = sum(int(i.get("quantity", 0)) for i in items)
    return {"subtotal": subtotal, "count": count}

def gen_order_no() -> str:
    return datetime.now(timezone.utc).strftime("ODR%Y%m%d") + secrets.token_hex(4).upper()


@router.get("/cart")
async def get_cart():
    return FileResponse(STATIC_DIR / "Product" / "cart.html")

# 取得購物車（前端用這個拉資料）
@router.get("/api/cart")
async def get_cart_api(current: dict = Depends(get_current_user),carts_collection = Depends(carts_col),):
    # get_current_user 已經保證有登入，不需要再 _require_login
    account = current["account"]  # 只信 JWT 裡的 account

    cart = await carts_collection.find_one(
        {"account": account, "status": "active"},
        {"_id": 0},
    )

    items = cart.get("items", []) if cart else []
    return {
        "cart": items,
        "total": _totals(items),
    }



# 加入/累加購物車
@router.post("/api/cart", status_code=201)
async def add_to_cart(
    body: AddToCartRequest,
    current: dict = Depends(get_current_user),
    products_collection = Depends(products_col),
    carts_collection = Depends(carts_col),
):
    # 這裡一定是有登入的使用者（get_current_user 已檢查）
    account = current["account"]

    name = body.name      # 已經 strip + 檢查不得為空
    quantity = body.quantity  # 至少 1，因為 Field(ge=1)

    # 確認商品存在
    product = await products_collection.find_one({"name": name}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")

    price = int(product.get("price", 0))

    # 找使用者的 active 購物車
    cart = await carts_collection.find_one(
        {"account": account, "status": "active"},
        {"_id": 0},
    )
    items = cart.get("items", []) if cart else []

    # 3️⃣ 如果商品已在購物車裡 → 累加數量；否則新增一筆
    for it in items:
        if it["name"] == name:
            it["quantity"] = int(it.get("quantity", 0)) + quantity
            it["price"] = price  # 價格以現在商品價格為準
            break
    else:
        items.append({
            "name": name,
            "quantity": quantity,
            "price": price,
            "img": product.get("img"),
        })

    # 4️⃣ 寫回 DB（upsert：第一次也會建立）
    await carts_collection.update_one(
        {"account": account, "status": "active"},
        {
            "$set": {
                "items": items,
                "account": account,
                "status": "active",
            }
        },
        upsert=True,
    )

    return {
        "success": True,
        "cart": items,
        "total": _totals(items),
    }

@router.delete("/api/cart/items/{name}")
async def remove_from_cart(
    name: str,
    current: dict = Depends(get_current_user),
    carts_collection = Depends(carts_col),
):
    # 只信 JWT 拿 account（get_current_user 已經確保有登入）
    account = current["account"]

    filter_ = {"account": account, "status": "active"}

    # 用 $pull 把 items 陣列裡 name=指定值 的項目移除
    result = await carts_collection.update_one(
        filter_,
        {"$pull": {"items": {"name": name}}},
    )

    if result.modified_count == 0:
        # 沒有那個項目（或購物車不存在）
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="項目不存在或購物車不存在",
        )

    # 回傳最新購物車內容給前端
    cart = await carts_collection.find_one(filter_, {"_id": 0, "items": 1})

    items = cart.get("items", []) if cart else []
    return {
        "success": True,
        "cart": items,
        "total": _totals(items),
    }



@router.patch("/api/cart/items/{name}")
async def set_quantity(
    name: str,
    body: SetQuantityRequest,
    current: dict = Depends(get_current_user),
    carts_collection = Depends(carts_col),
):
    account = current["account"]

    qty = body.quantity  # 一定 >= 1（前端也保證 >0）

    result = await carts_collection.update_one(
        {"account": account, "status": "active", "items.name": name},
        {"$set": {"items.$.quantity": qty}},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="項目不存在",
        )

    cart = await carts_collection.find_one(
        {"account": account, "status": "active"},
        {"_id": 0, "items": 1},
    )

    items = cart.get("items", []) if cart else []
    return {
        "cart": items,
        "total": _totals(items),
    }

# 清空購物車
@router.delete("/api/cart")
async def clear_cart(
    current: dict = Depends(get_current_user),
    carts_collection = Depends(carts_col),
):
    account = current["account"]  # 一律信 JWT 內的 account

    filter_ = {"account": account, "status": "active"}

    await carts_collection.update_one(
        filter_,
        {"$set": {"items": []}},
        upsert=False,  # 清空通常不需要幫你建立新車
    )

    # 策略 A：永遠回空車（前端處理最簡單）
    return {
        "success": True,
        "cart": [],
        "total": {"subtotal": 0, "count": 0},
    }

# === 1) 建立結帳（checkout） ===
@router.post("/api/checkout")
async def create_checkout_session(
    current: dict = Depends(get_current_user),
    carts_collection = Depends(carts_col),
):
    account = current["account"]

    cart = await carts_collection.find_one(
        {"account": account, "status": "active"},
        {"_id": 0},
    )
    items = (cart or {}).get("items") or []

    if not items:
        raise HTTPException(status_code=400, detail="購物車為空")

    total = _totals(items)  # 你的實作是 dict: {"subtotal": ..., "count": ...}
    amount = int(total["subtotal"])

    if amount <= 0:
        raise HTTPException(status_code=400, detail="金額錯誤")

    # 2) 建立訂單號（寫在 cart 上，當作 pending 訂單）
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
        upsert=False,  # 若沒有 active cart 通常代表流程有問題（items 都清掉了）
    )

    # 3) 組 ECPay 欄位（ChoosePayment=ALL）
    params = {
        "MerchantTradeNo": order_id,
        "MerchantTradeDate": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        "PaymentType": "aio",
        "TotalAmount": amount,
        "TradeDesc": "TEST ORDER",
        "ItemName": "#".join(i.get("name", "") for i in items) or "訂單",
        "ChoosePayment": "ALL",
        "ReturnURL": f"{BASE_URL}/payment/notify",      # Webhook（要公網）
        "OrderResultURL": f"{BASE_URL}/payment/return", # 導回頁（可本機）
        "ClientBackURL": f"{FRONTEND_BASE_URL}/",
        "NeedExtraPaidInfo": "Y",
        "EncryptType": 1,
    }

    fields = sdk.create_order(params)
    return {
        "action": ECPAY_STAGE,
        "method": "POST",
        "fields": fields,
    }


# === 2) ECPay 付款通知（Webhook） ===
@router.post("/payment/notify", response_class=PlainTextResponse)
async def ecpay_notify(
    request: Request,
    carts_collection = Depends(carts_col),
):
    form = dict((await request.form()).items())

    merchant_trade_no = form.get("MerchantTradeNo")
    rtn_code = str(form.get("RtnCode", ""))
    logger.info("[ECPAY] notify arrive no=%s rtn=%s", merchant_trade_no, rtn_code)

    # 1) 驗簽
    try:
        if not sdk.verify_notify_mac(form):
            logger.error("[ECPAY] BAD_MAC no=%s payload=%s", merchant_trade_no, form)
            return PlainTextResponse("0|FAIL")
    except Exception as e:
        logger.exception("[ECPAY] MAC_EXCEPTION no=%s err=%s payload=%s", merchant_trade_no, e, form)
        return PlainTextResponse("0|FAIL")

    # 2) 解析金額
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

    # 4) 若非 pending
    status_now = cart.get("status")
    if status_now != "pending":
        logger.info("[ECPAY] NON_PENDING no=%s status=%s -> idempotent OK", merchant_trade_no, status_now)
        return PlainTextResponse("1|OK")

    # 5) 金額比對
    try:
        expect_amt = int(cart.get("amount_snapshot", -1))
    except Exception:
        expect_amt = -1
    if expect_amt != trade_amt:
        logger.warning("[ECPAY] AMOUNT_MISMATCH no=%s expect=%s got=%s", merchant_trade_no, expect_amt, trade_amt)
        return PlainTextResponse("0|FAIL")

    # 6) 準備更新
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
        {"$set": updates},
    )
    logger.info(
        "[ECPAY] UPDATE no=%s matched=%s modified=%s -> %s",
        merchant_trade_no, res.matched_count, res.modified_count, updates["status"],
    )

    # 7) 一定回 1|OK
    return PlainTextResponse("1|OK")


# === 3) ECPay 導回頁（使用者付款後跳回來） ===
@router.api_route("/payment/return", methods=["POST"])
async def payment_return():
    # 你原本就是直接回首頁 HTML
    return FileResponse(STATIC_DIR/ "home.html")