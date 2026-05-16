"""Agente Morgan: Orquestador de la lógica con Agno."""
from __future__ import annotations

import json
import logging

from agno.agent import Agent
from agno.models.groq import Groq
# En agno > 2.0.0, la persistencia se maneja de forma distinta, 
# por lo que de momento ejecutamos el agente sin 'storage' para evitar el error de Render.

from app.agent.prompts.system_prompt import SYSTEM_PROMPT
from app.core.config import settings
from app.integrations.notion import (
    create_patient_in_notion,
    get_copay_for_plan,
    get_hospitals_by_specialty,
    get_patient_plan,
)
from app.services.hospital_network import rank_hospitals

logger = logging.getLogger(__name__)

# Herramientas
async def register_patient_tool(patient_id: str, nombre: str, plan_nombre: str) -> str:
    result = await create_patient_in_notion(patient_id, nombre, plan_nombre)
    return f"¡Listo! {nombre} registrado." if result else "Error al registrar."

async def get_patient_plan_tool(patient_id: str) -> str:
    plan = await get_patient_plan(patient_id)
    return json.dumps(plan, ensure_ascii=False) if plan else "No encontrado."

async def calculate_copay_tool(patient_id: str, especialidad: str) -> str:
    plan = await get_patient_plan(patient_id)
    if not plan: return "Paciente no encontrado."
    res = await get_copay_for_plan(plan["plan_nombre"], especialidad)
    return json.dumps(res, ensure_ascii=False)

async def get_network_hospitals_tool(especialidad: str, user_lat: float = None, user_lon: float = None) -> str:
    hospitals = await get_hospitals_by_specialty(especialidad)
    ranked = rank_hospitals(hospitals, user_lat, user_lon)
    return json.dumps(ranked, ensure_ascii=False)

def build_agent(session_id: str = None) -> Agent:
    return Agent(
        model=Groq(id=settings.groq_model, api_key=settings.groq_api_key, temperature=0.1),
        system_message=SYSTEM_PROMPT,
        tools=[register_patient_tool, get_patient_plan_tool, calculate_copay_tool, get_network_hospitals_tool],
        add_history_to_context=True,
        session_id=session_id,
    )

async def run_chat(message: str, session_id: str, patient_id: str = None, lat: float = None, lon: float = None) -> dict:
    ctx = f"[PACIENTE: {patient_id} | GPS: {lat}, {lon}]\n" if patient_id or lat else ""
    agent = build_agent(session_id)
    try:
        resp = await agent.arun(ctx + message)
        # Limpiamos posibles respuestas JSON de error que se cuelan como contenido
        text = resp.content if hasattr(resp, "content") else str(resp)
        if "rate_limit_exceeded" in text or "tokens_per_minute" in text:
            text = "Morgan está procesando mucha información. Por favor, reintenta en 2 segundos. ⏳"
        return {"response": text, "session_id": session_id}
    except Exception as e:
        logger.error(f"Error: {e}")
        return {"response": "Lo siento, Morgan tuvo un hipo técnico. ¡Reintenta ahora!", "session_id": session_id}
