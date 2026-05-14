"""Lógica de negocio: copagos, cobertura por plan."""
from __future__ import annotations

import logging

from app.integrations.notion import (
    get_copay_for_plan,
    get_hospitals_by_specialty,
    get_patient_plan,
)

logger = logging.getLogger(__name__)


async def calculate_copay(
    patient_id: str,
    especialidad: str,
    costo_estimado: float | None = None,
) -> dict:
    """
    Calcula el copago real del paciente para una especialidad dada.

    Returns dict con:
      - patient: datos del paciente/plan
      - copay_info: reglas del copago del plan
      - monto_copago: cantidad a pagar por el paciente
      - hospitales: hospitales en red que cubren la especialidad
    """
    patient = await get_patient_plan(patient_id)
    if not patient:
        return {
            "error": f"No se encontró el paciente con ID: {patient_id}",
            "monto_copago": None,
            "hospitales": [],
        }

    plan_id = patient.get("plan_id", "")
    copay_info = await get_copay_for_plan(plan_id, especialidad)
    hospitales = await get_hospitals_by_specialty(especialidad)

    # Calcular monto de copago
    monto_copago: float | None = None
    if copay_info:
        copago_fijo = copay_info.get("copago_fijo") or 0.0
        copago_porcentaje = copay_info.get("copago_porcentaje") or 0.0
        tope = copay_info.get("tope_bolsillo")

        if copago_fijo > 0:
            monto_copago = copago_fijo
        elif copago_porcentaje > 0 and costo_estimado:
            monto_copago = round(costo_estimado * (copago_porcentaje / 100), 2)
            if tope and monto_copago > tope:
                monto_copago = tope
        else:
            # Usar copago_base del plan como fallback
            base_pct = patient.get("copago_base") or 20.0
            if costo_estimado:
                monto_copago = round(costo_estimado * (base_pct / 100), 2)

    return {
        "patient": patient,
        "copay_info": copay_info,
        "monto_copago": monto_copago,
        "hospitales": hospitales,
    }
