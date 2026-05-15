"""Webhook de WhatsApp (vía Twilio) para recibir mensajes y responder con el agente Morgan."""
import logging
from fastapi import APIRouter, Request, Response
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse

from app.agent.copay_agent import run_chat
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/webhook", summary="Webhook de WhatsApp (Twilio)")
async def whatsapp_webhook(request: Request):
    """
    Recibe mensajes de WhatsApp desde Twilio y responde usando el agente Morgan.
    """
    # Twilio envía los datos como form-data (application/x-www-form-urlencoded)
    form_data = await request.form()
    
    incoming_msg = form_data.get("Body", "").strip()
    sender_number = form_data.get("From", "") # Ej: whatsapp:+593987654321

    if not incoming_msg:
        return Response(status_code=200)

    logger.info(f"Mensaje de WhatsApp recibido de {sender_number}: {incoming_msg}")

    # Usamos el número de teléfono como session_id para mantener el contexto por paciente
    session_id = f"whatsapp_{sender_number}"

    # Procesamos el mensaje con el agente
    result = await run_chat(incoming_msg, session_id=session_id)
    bot_response = result["response"]

    # Crear respuesta en formato TwiML para Twilio
    twiml_resp = MessagingResponse()
    twiml_resp.message(bot_response)

    return Response(content=str(twiml_resp), media_type="application/xml")
