"""Conversación con el agente (síntoma → especialidad → copago)."""
from fastapi import APIRouter, HTTPException

from app.agent.copay_agent import run_chat
from app.schemas.patient import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/", response_model=ChatResponse, summary="Enviar mensaje al agente")
async def chat_message(body: ChatRequest) -> ChatResponse:
    """
    Recibe un mensaje del usuario y lo procesa con el agente Agno+Groq.
    Mantiene el contexto conversacional a través del session_id.
    """
    # Prepend patient_id al mensaje si se provee y no está en el mensaje
    message = body.message
    if body.patient_id and body.patient_id not in message:
        message = f"[Mi ID de paciente es: {body.patient_id}]\n{message}"

    try:
        result = await run_chat(message, session_id=body.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        response=result["response"],
        session_id=result.get("session_id"),
    )
