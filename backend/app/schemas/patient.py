"""Modelos Pydantic: síntoma, plan, respuesta de estimación."""
from __future__ import annotations

from pydantic import BaseModel, Field


# ── Request schemas ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Mensaje del usuario al agente.")
    session_id: str | None = Field(
        default=None,
        description="ID de sesión para mantener el contexto conversacional.",
    )
    patient_id: str | None = Field(
        default=None,
        description="ID del paciente (opcional, el agente lo pedirá si no se provee).",
    )


class EstimateRequest(BaseModel):
    patient_id: str = Field(..., description="Identificador único del paciente.")
    symptom: str = Field(..., description="Descripción del síntoma o motivo de consulta.")
    costo_estimado: float | None = Field(
        default=None,
        description="Costo estimado de la consulta en USD (opcional).",
    )


# ── Response schemas ──────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    response: str
    session_id: str | None = None


class HospitalInfo(BaseModel):
    hospital_id: str
    nombre: str
    ciudad: str
    nivel: str
    especialidades: list[str]
    en_red: bool


class PatientPlanInfo(BaseModel):
    patient_id: str | None = None
    nombre: str | None = None
    plan_id: str | None = None
    plan_nombre: str | None = None
    deducible_anual: float | None = None
    deducible_cubierto: float | None = None
    copago_base: float | None = None


class EstimateResponse(BaseModel):
    especialidad_sugerida: str | None = None
    patient: PatientPlanInfo | None = None
    monto_copago: float | None = None
    copago_info: dict | None = None
    hospitales: list[HospitalInfo] = []
    error: str | None = None
