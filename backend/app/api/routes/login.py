from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from app.core.paths import STATIC_DIR
from app.core.db import users_col
from app.crud import get_user_by_account
from app.core.security import create_jwt, decode_jwt  # 你自己的 jwt 工具
from passlib.context import CryptContext

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginData(BaseModel):
    account: str
    password: str

@router.get("/login")
async def get_login_page():
    return FileResponse(STATIC_DIR /"User"/"login.html")

@router.post("/api/login")
async def login(data: LoginData, users = Depends(users_col)):
    user = await get_user_by_account(users, data.account)
    if not user:
        return JSONResponse(
            status_code=400,
            content={"error": "帳號或密碼錯誤"}
        )

    # 3. 密碼比對（DB 裡 password 要是 bcrypt hash）
    if not pwd_context.verify(data.password, user.get("password", "")):
        return JSONResponse(
            status_code=400,
            content={"error": "帳號或密碼錯誤"}
        )
    payload = {"account": user["account"], "username": user["username"], "level": int(user["level"])}
    token = create_jwt(payload, expires_in=10)  # 你原本的 10 秒
    return JSONResponse(content={"message": "登入成功", "token": token})

@router.get("/api/user")
async def get_user(request: Request):
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        return JSONResponse(content={"username": None})
    token = auth.removeprefix("Bearer ").strip()
    data = decode_jwt(token)
    if not data:
        return JSONResponse(content={"username": None})
    return JSONResponse(content={"username": data["username"], "level": data["level"]})
