from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse
from app.core.db import products_col
from app.api.deps import get_jwt_payload_optional
from app.core.paths import STATIC_DIR
from app.crud import get_all_products

router = APIRouter(tags=["products"])

@router.get("/products")
async def serve_product_page():
    return FileResponse(STATIC_DIR/"Product"/"products.html")

@router.get("/api/products")
async def get_product_page(products_collection = Depends(products_col),  payload: dict | None = Depends(get_jwt_payload_optional)):
    products = await get_all_products(products_collection)
    viewer = payload.get("account") if payload else None
    return JSONResponse(content={
        "products": products,  "viewer": viewer
    })