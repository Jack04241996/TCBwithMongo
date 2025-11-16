from fastapi import APIRouter

from app.api.routes import products, login, users, carts , register, products_management, story, home


api_router = APIRouter()
api_router.include_router(home.router)
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(carts.router)
api_router.include_router(products.router)
api_router.include_router(products_management.router)
api_router.include_router(register.router)
api_router.include_router(story.router)

