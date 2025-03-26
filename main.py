from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from apis.main import routers
from emails.utils import _redis

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    _redis.close()


app = FastAPI(title="AI Chat API", version="1.0.0")
# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(routers, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "ok"}