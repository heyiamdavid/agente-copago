"""Conversación con el agente (síntoma → especialidad → copago)."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def chat_message():
    # TODO: integrar agente Agno + Groq
    return {"message": "pendiente"}
