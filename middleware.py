from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from database import users_collection
from jwt_handler import decode_jwt
from functools import wraps
from fastapi import status

class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token = request.headers.get("Authorization")  # 取得 Authorization header
        if token and token.startswith("Bearer "):     # 確保格式正確
            jwt_token = token[7:]  # 去掉 "Bearer " 的前綴，取出 token 本體
            payload = decode_jwt(jwt_token)  # 嘗試解碼 JWT
            if payload:
                request.state.user = payload  # 驗證成功，把 user 訊息放進 request.state
            else:
                request.state.user = None     # 驗證失敗
        else:
            request.state.user = None         # 沒有提供 token
        return await call_next(request)

def require_level(levels : list[int]):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = getattr(request.state, "user", None)
            if not user:
                return RedirectResponse("/login", status_code=302)
            if user["level"] not in levels:
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Permission denied"}
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator