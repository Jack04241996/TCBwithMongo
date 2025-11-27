
import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.main import api_router
from app.core.config import settings
from app.core.paths import STATIC_DIR, IMAGE_DIR

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}" if route.tags else route.name



if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.API_V1_STR else "/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
)

# ✅ 用絕對路徑（或 Path）掛靜態檔案
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/image", StaticFiles(directory=IMAGE_DIR), name="image")

# if settings.all_cors_origins: 前端分離用
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=settings.all_cors_origins,
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )

app.include_router(api_router)  #, prefix=settings.API_V1_STR

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
