"""Agrupa routers v1."""
from fastapi import APIRouter

from app.api.v1.routes import chat, estimate

api_router = APIRouter(prefix="/v1")
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(estimate.router, prefix="/estimate", tags=["estimate"])
