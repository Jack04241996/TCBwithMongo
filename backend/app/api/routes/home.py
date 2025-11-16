from fastapi.responses import FileResponse
from fastapi import APIRouter
from app.core.paths import STATIC_DIR

router = APIRouter(tags=["home"])

@router.get("/")
async def serve_home_page():
    return FileResponse(STATIC_DIR/"home.html")