from fastapi import APIRouter

from app.auth.router import router as auth_router
from app.api.v1.tickers import router as tickers_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.chat import router as chat_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router)
api_v1_router.include_router(tickers_router)
api_v1_router.include_router(ingestion_router)
api_v1_router.include_router(chat_router)
