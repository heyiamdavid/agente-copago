"""Agrupa routers v1."""
from fastapi import APIRouter

from app.api.v1.routes import chat, estimate, telegram, whatsapp

api_router = APIRouter(prefix="/v1")
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(estimate.router, prefix="/estimate", tags=["estimate"])
api_router.include_router(telegram.router, prefix="/telegram", tags=["telegram"])
api_router.include_router(whatsapp.router, prefix="/whatsapp", tags=["whatsapp"])
