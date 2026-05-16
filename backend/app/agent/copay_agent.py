"""Orquestación del agente: síntoma → especialidad → herramientas de copago/red.

Usa el framework Agno con el modelo Groq openai/gpt-oss-120b.
El agente tiene tres herramientas:
  - get_patient_plan_tool     → obtiene datos del plan desde Notion
  - calculate_copay_tool      → calcula el copago real
  - get_network_hospitals_tool → lista hospitales en red
"""
from __future__ import annotations

import json
import logging

from agno.agent import Agent
from agno.models.groq import Groq
from agno.db.sqlite import SqliteDb

from app.agent.prompts.system_prompt import SYSTEM_PROMPT
from app.core.config import settings
from app.integrations.notion import (
    get_copay_for_plan,
    get_hospitals_by_specialty,
    get_patient_plan,
    create_patient_in_notion,
)
from app.services.hospital_network import rank_hospitals
from app.services.insurance import calculate_copay

logger = logging.getLogger(__name__)

# ── Herramientas para el agente ───────────────────────────────────────────────

async def register_patient_tool(patient_id: str, nombre: str, plan_nombre: str) -> str:
    """
    Registra a un nuevo paciente en la base de datos de Notion.
    Usa esta herramienta cuando un paciente intente consultar su cobertura
    pero su ID no se encuentre en la base de datos.

    Args:
        patient_id: Número de identidad proporcionado por el usuario.
        nombre: Nombre completo del paciente.
        plan_nombre: Nombre del plan de seguro médico (ej. Bupa, Saludsa, etc).

    Returns:
        JSON con el resultado del registro.
    """
    result = await create_patient_in_notion(patient_id, nombre, plan_nombre)
    if result is None:
        return json.dumps({"error": "No se pudo registrar al paciente debido a un error técnico."})
    return json.dumps({"status": "success", "message": "Paciente registrado exitosamente.", "data": result}, ensure_ascii=False)


async def get_patient_plan_tool(patient_id: str) -> str:
    """
    Obtiene el plan de seguro del paciente dado su ID.

    Args:
        patient_id: Identificador único del paciente.

    Returns:
        JSON con los datos del plan del paciente.
    """
    result = await get_patient_plan(patient_id)
    if result is None:
        return json.dumps({"error": f"No se encontró el paciente: {patient_id}. Por favor, pregúntale su nombre y plan para registrarlo usando register_patient_tool."})
    return json.dumps(result, ensure_ascii=False)


async def calculate_copay_tool(
    patient_id: str,
    especialidad: str,
    costo_estimado: float | None = None,
) -> str:
    """
    Calcula el copago estimado para un paciente en una especialidad médica.

    Args:
        patient_id: Identificador único del paciente.
        especialidad: Especialidad médica (ej. 'Cardiología', 'Neurología').
        costo_estimado: Costo estimado de la consulta en USD (opcional).

    Returns:
        JSON con los datos del copago calculado.
    """
    result = await calculate_copay(patient_id, especialidad, costo_estimado)
    return json.dumps(result, ensure_ascii=False, default=str)


async def get_network_hospitals_tool(especialidad: str, user_lat: float | None = None, user_lon: float | None = None) -> str:
    """
    Lista los hospitales en red que atienden una especialidad médica,
    ordenados por cercanía geográfica (si se provee ubicación) y nivel.

    Args:
        especialidad: Especialidad médica a buscar.
        user_lat: Latitud actual del usuario (opcional).
        user_lon: Longitud actual del usuario (opcional).

    Returns:
        JSON con la lista de hospitales en red ordenados.
    """
    hospitales = await get_hospitals_by_specialty(especialidad)
    ranked = rank_hospitals(hospitales, user_lat, user_lon)
    return json.dumps(ranked, ensure_ascii=False, default=str)


# ── Construcción del agente ───────────────────────────────────────────────────

def build_agent(session_id: str | None = None) -> Agent:
    """Construye y retorna un agente Agno con Groq, herramientas necesarias y persistencia en SQLite."""
    return Agent(
        model=Groq(
            id=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.2,
            top_p=0.9,
            max_tokens=1024,
        ),
        system_message=SYSTEM_PROMPT,
        tools=[
            register_patient_tool,
            get_patient_plan_tool,
            calculate_copay_tool,
            get_network_hospitals_tool,
        ],
        db=SqliteDb(db_file="agent_storage.db"),
        add_history_to_context=True,
        markdown=False,
        session_id=session_id,
    )


async def run_chat(
    message: str, 
    session_id: str | None = None,
    lat: float | None = None,
    lon: float | None = None
) -> dict:
    """
    Ejecuta un turno de conversación con el agente.

    Args:
        message: Mensaje del usuario.
        session_id: ID de sesión para mantener contexto entre turnos.
        lat: Latitud del usuario.
        lon: Longitud del usuario.

    Returns:
        dict con 'response' (str) y 'session_id' (str).
    """
    # Si tenemos ubicación, la inyectamos sutilmente en el mensaje para que el agente la use
    if lat and lon:
        message = f"[UBICACIÓN ACTUAL: {lat}, {lon}]\n{message}"

    agent = build_agent(session_id)
    try:
        run_response = await agent.arun(message)
        response_text = run_response.content if hasattr(run_response, "content") else str(run_response)
    except Exception as exc:
        logger.exception("Error en el agente: %s", exc)
        response_text = (
            "Lo siento, ocurrió un error al procesar tu solicitud. "
            "Por favor intenta de nuevo."
        )

    return {
        "response": response_text,
        "session_id": agent.session_id or session_id,
    }
