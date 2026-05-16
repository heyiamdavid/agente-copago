"""Webhook de Telegram para recibir mensajes y responder con el agente Morgan."""
from __future__ import annotations

import logging
import httpx
from fastapi import APIRouter, Request, Response

from app.agent.copay_agent import run_chat
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

async def _send_message(chat_id: int, text: str) -> None:
    """Envía un mensaje de texto al chat de Telegram indicado."""
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Error enviando mensaje a Telegram: {e}")

@router.post("/webhook", summary="Webhook de Telegram")
async def telegram_webhook(request: Request) -> Response:
    """
    Recibe actualizaciones (mensajes) de Telegram y las procesa con el agente Morgan.
    """
    if not settings.telegram_bot_token:
        return Response(status_code=200)

    try:
        update = await request.json()
    except Exception:
        return Response(status_code=200)

    message = update.get("message") or update.get("edited_message")
    if not message:
        return Response(status_code=200)

    chat_id: int = message["chat"]["id"]
    text: str = message.get("text", "").strip()
    location = message.get("location")
    
    lat = location.get("latitude") if location else None
    lon = location.get("longitude") if location else None

    # Usamos el chat_id como session_id
    session_id = f"telegram_{chat_id}"

    # Saludo inicial
    if text.startswith("/start"):
        welcome_msg = (
            "¡Hola! Soy *Morgan*, tu asistente de copagos en Ecuador. 🏥🇪🇨\n\n"
            "Puedo ayudarte a calcular tu copago y encontrar hospitales cercanos.\n\n"
            "📍 *Tip:* Envíame tu ubicación actual (clip -> Ubicación) para decirte qué hospitales tienes más cerca.\n\n"
            "🌐 También puedes usar mi versión web con mapa interactivo en: https://hey-morgan.vercel.app"
        )
        await _send_message(chat_id, welcome_msg)
        return Response(status_code=200)

    if not text and not location:
        return Response(status_code=200)

    # Si solo mandó ubicación sin texto
    if location and not text:
        text = "Busca hospitales cerca de mi ubicación actual"

    # Procesamos el mensaje con el agente
    result = await run_chat(text, session_id=session_id, lat=lat, lon=lon)
    await _send_message(chat_id, result["response"])

    return Response(status_code=200)
