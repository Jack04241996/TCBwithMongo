from typing import Any, Dict, List, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from app.core.security import decode_jwt 
from app.core.db import users_col

async def get_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    token = auth.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token

# 解 JWT → payload（必須登入）
async def get_jwt_payload(token: str = Depends(get_bearer_token)) -> Dict[str, Any]:
    payload = decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid or expired")
    return payload

async def get_bearer_token_optional(request: Request) -> str | None:
    a = request.headers.get("Authorization", "")
    return a.removeprefix("Bearer ").strip() if a.startswith("Bearer ") else None

async def get_jwt_payload_optional(token: str | None = Depends(get_bearer_token_optional)) -> dict | None:
    return decode_jwt(token) if token else None

# 權限：level 必須在指定清單（API 風格：沒權限回 403）
def require_level_api(levels: List[int]):
    async def checker(payload: Dict[str, Any] = Depends(get_jwt_payload)):
        try:
            lvl = int(payload.get("level", -1))
        except (TypeError, ValueError):
            lvl = -1
        if lvl not in levels:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
        return True  # 讓 FastAPI 知道檢查通過
    return checker

# 頁面路由版：沒登入/沒權限→轉跳 /login（跟你原 decorator 行為一致）
def require_level_page(levels: List[int]):
    async def checker(request: Request, payload: Optional[Dict[str, Any]] = Depends(get_jwt_payload)):
        if not payload:
            return RedirectResponse("/login", status_code=302)
        try:
            lvl = int(payload.get("level", -1))
        except (TypeError, ValueError):
            lvl = -1
        if lvl not in levels:
            return RedirectResponse("/login", status_code=302)
        return True
    return checker

async def get_current_user(
    payload: Dict[str, Any] = Depends(get_jwt_payload),
    users = Depends(users_col),
    ) -> Dict[str, Any]:
    account = payload.get("account")
    if not account:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await users.find_one({"account": account})
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # 可選：若你有 is_active 欄位
    if user.get("is_active") is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")

    return user