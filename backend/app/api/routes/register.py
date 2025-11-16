# register.py
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse
from app.core.db import users_col
from app.crud import user_exists, create_user
from app.core.paths import STATIC_DIR
from app.models import RegisterData
router = APIRouter(tags=["register"])



@router.get("/build")
async def get_build_page():
    return FileResponse(STATIC_DIR/"User"/"build.html")

@router.post("/api/register")
async def register_user(body: RegisterData, users = Depends(users_col)):
    # 唯一性檢查（任何一個撞到就回 400）
    if await user_exists(users, {"email": body.email}):
        return JSONResponse(status_code=400, content={"error": "Email已存在，請重新輸入"})
    if await user_exists(users, {"account": body.account}):
        return JSONResponse(status_code=400, content={"error": "帳號已存在，請重新輸入"})
    if await user_exists(users, {"phone": body.phone}):
        return JSONResponse(status_code=400, content={"error": "電話已存在，請重新輸入"})

    # 建立使用者（在 CRUD 內負責雜湊密碼）
    await create_user(
        users,
        account=body.account,
        username=body.username,
        password=body.password,
        phone=body.phone,
        email=body.email,
        level=0,
    )
    return JSONResponse(status_code=201, content={"message": "註冊成功"})
