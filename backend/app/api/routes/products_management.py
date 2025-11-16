from fastapi import APIRouter, Depends,  HTTPException , status
from fastapi.responses import FileResponse, JSONResponse
from app.core.db import products_col
from pydantic import BaseModel
from app.api.deps import  require_level_api, get_jwt_payload
from app.core.paths import STATIC_DIR
from app.crud import get_all_products , delete_product_by_name , update_product , create_product, product_name_exists, get_product_by_name

router = APIRouter(tags=["products_management"])

@router.get("/products_management")
async def serve_product_management_page():
    return FileResponse(STATIC_DIR/"Product"/"products_management.html")

@router.get("/api/products_management", dependencies=[Depends(require_level_api([2,3]))])
async def get_product_management_page(products_collection = Depends(products_col),  payload: dict | None = Depends(get_jwt_payload)):
    products = await get_all_products(products_collection)
    viewer = payload.get("account")
    return JSONResponse(content={
        "products": products, "viewer": viewer
    })

@router.delete("/api/products_delete/{name}", dependencies=[Depends(require_level_api([3]))])
async def delete_product(
    name: str,
    products_collection = Depends(products_col),
):
    await delete_product_by_name(products_collection, name)
    return JSONResponse(status_code=200, content={"message": "刪除成功"})
    
@router.get("/products_edit/{name}")
async def serve_product_edit_page(name: str):
    return FileResponse(STATIC_DIR/"Product"/"products_edit.html")

@router.get("/api/products_edit/{name}", dependencies=[Depends(require_level_api([3]))])
async def edit_product(name: str,products_collection = Depends(products_col)):
    product = await get_product_by_name(products_collection, name)
    return JSONResponse(content={"products": product})

class ProductUpdate(BaseModel):
    price: int | None = None
    description: str | None = None
    img: str | None = None

@router.patch("/api/products_edit/{name}", dependencies=[Depends(require_level_api([3]))])
async def update_product(
    name: str,
    body: ProductUpdate,
    products_collection = Depends(products_col),
):
    # 組更新欄位：只保留不是 None 的
    update_fields = {
        k: v for k, v in body.model_dump().items() if v is not None
    }

    await update_product(products_collection, name, update_fields)

    return {"message": "編輯成功"}


@router.get("/products_build")
async def serve_product_build_page():
    return FileResponse(STATIC_DIR/"Product"/"products_build.html")   

class ProductBuild(BaseModel):
    name: str 
    price: int 
    description: str 
    img: str 

@router.post("/api/products_build", dependencies=[Depends(require_level_api([2, 3]))])
async def register_product(
    body: ProductBuild,
    products_collection = Depends(products_col),
):
    name = body.name.strip()
    img = body.img.strip()
    description = body.description.strip()
    price = body.price  # 已經是 int

    # 1️⃣ 基本必填檢查（這還是屬於「輸入驗證」，放在 route 比較合理）
    if not all([name, img, description]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="所有欄位皆為必填，請勿留空或只填空白",
        )

    # 2️⃣ 呼叫 CRUD 檢查名稱是否已存在
    if await product_name_exists(products_collection, name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="商品名稱已存在，請重新輸入",
        )

    # 3️⃣ 呼叫 CRUD 建立商品
    await create_product(
        products_collection,
        name=name,
        price=price,
        img=img,
        description=description,
    )

    return {"message": "新增成功"}