from fastapi import APIRouter, Depends ,  HTTPException , status
from fastapi.responses import FileResponse, JSONResponse
from app.api.deps import  require_level_api ,  get_jwt_payload , get_current_user
from app.core.db import users_col
from app.models import UserUpdate
from app.core.paths import STATIC_DIR
from app.crud import delete_user_by_account , update_user_by_account

router = APIRouter(tags=["users"])




@router.get("/users_management" )
async def serve_users_page():
    return FileResponse(STATIC_DIR/"User"/"users_management.html")

@router.get("/api/users_management" , dependencies=[Depends(require_level_api([2,3]))])
async def user_list(users_collection = Depends(users_col)):
    users = await users_collection.find({}, {"_id": 0}).to_list(length=None)
    return JSONResponse(content= {    
        "users": users         
    })

# 刪除使用者
@router.delete("/api/user_delete/{account}", dependencies=[Depends(require_level_api([3]))] )
async def delete_user(
    account: str,
    users_collection = Depends(users_col),
    current: dict = Depends(get_current_user),       # 由 DB 拿「目前使用者」
):
    if current.get("account") == account:
        raise HTTPException(status_code=400, detail="不能刪除自己的帳號")

    deleted = await delete_user_by_account(users_collection, account)

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="User not found")
    return {"message": "刪除成功"}
    
@router.get("/user_edit/{account}")
async def serve_users_edit_page(account: str):
    return FileResponse(STATIC_DIR/"User"/"user_edit.html")

# 編輯頁面
@router.get("/api/user_edit/{account}" , dependencies=[Depends(require_level_api([2,3]))])
async def edit_user(account: str , users_collection = Depends(users_col)):
    user = await users_collection.find_one({"account": account}, {"_id": 0})
    return JSONResponse(content={
        "user": user
    })

# 更新使用者
@router.patch("/api/user_edit/{account}" , dependencies=[Depends(require_level_api([2,3]))])
async def update_user(account: str, body: UserUpdate, users_collection = Depends(users_col) , payload: dict = Depends(get_jwt_payload),):
    update_fields = {
        "username": body.username,
        "phone": body.phone,
        "email": body.email,
    }

    # 只有等級 >= 3 才能修改 level
    if body.level is not None:
        caller_level = int(payload.get("level", 0))
        if caller_level < 3:
            raise HTTPException(status_code=403, detail="Not allowed to change level")
        update_fields["level"] = int(body.level)

    # 去掉 None 的欄位，避免把欄位設成 null
    update_fields = {k: v for k, v in update_fields.items() if v is not None}

    await update_user_by_account(users_collection, account, update_fields)
    return JSONResponse(status_code=200, content={"message": "編輯成功"})