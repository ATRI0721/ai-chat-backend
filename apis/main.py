from fastapi import APIRouter

from apis import auth, chat, user


routers = APIRouter()

routers.include_router(auth.router)
routers.include_router(chat.router)
routers.include_router(user.router)