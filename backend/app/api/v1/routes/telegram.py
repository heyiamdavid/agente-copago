"""Webhook de Telegram para recibir mensajes y responder con el agente Morgan."""
from __future__ import annotations

import logging

import httpx
from fastapi import APIRouter, Request, Response

from app.agent.copay_agent import run_chat
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

TELEGRAM_API = "https://api.telegram.org/bot{token}"


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
    Telegram envía un POST cada vez que el usuario escribe un mensaje.
    """
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN no configurado. Ignorando webhook.")
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

    if not text:
        return Response(status_code=200)

    # Usamos el chat_id como session_id para mantener contexto por usuario
    session_id = f"telegram_{chat_id}"

    # Si el usuario manda /start, le damos la bienvenida
    if text.startswith("/start"):
        await _send_message(
            chat_id,
            "¡Hola! Soy *Morgan*, tu asistente de copagos y cobertura médica. 🏥\n\n"
            "Cuéntame tu síntoma o pregunta sobre tu seguro. "
            "Para identificarte, en cualquier momento puedes escribir: "
            "`Mi ID es: 0912345678`"
        )
        return Response(status_code=200)

    # Procesamos el mensaje con el agente
    result = await run_chat(text, session_id=session_id)
    await _send_message(chat_id, result["response"])

    return Response(status_code=200)
