"""Modelos Pydantic: síntoma, plan, respuesta de estimación."""
from pydantic import BaseModel


class SymptomInput(BaseModel):
    description: str
    insurance_plan_id: str | None = None
