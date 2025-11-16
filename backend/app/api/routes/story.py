from fastapi.responses import FileResponse
from fastapi import APIRouter
from app.core.paths import STATIC_DIR

router = APIRouter(tags=["story"])

@router.get("/story")
async def story():
    return FileResponse(STATIC_DIR/"story.html")