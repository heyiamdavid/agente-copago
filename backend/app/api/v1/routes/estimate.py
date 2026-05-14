"""Estimación explícita de copago / hospital en red (endpoint directo)."""
from fastapi import APIRouter, HTTPException

from app.schemas.patient import EstimateRequest, EstimateResponse
from app.services.hospital_network import guess_specialty_from_symptom, rank_hospitals
from app.services.insurance import calculate_copay

router = APIRouter()


@router.post("/", response_model=EstimateResponse, summary="Estimar copago directamente")
async def estimate(body: EstimateRequest) -> EstimateResponse:
    """
    Endpoint directo (sin conversación) que calcula el copago para un
    paciente dado un síntoma y, opcionalmente, un costo estimado.

    Útil para integraciones directas o pruebas sin pasar por el chat.
    """
    # Intentar mapear síntoma → especialidad con heurística
    especialidad = guess_specialty_from_symptom(body.symptom)
    if not especialidad:
        especialidad = "Medicina General"  # fallback

    try:
        result = await calculate_copay(
            patient_id=body.patient_id,
            especialidad=especialidad,
            costo_estimado=body.costo_estimado,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if "error" in result and result["error"]:
        return EstimateResponse(
            especialidad_sugerida=especialidad,
            error=result["error"],
        )

    # Rankear hospitales
    hospitales_raw = result.get("hospitales", [])
    hospitales_ranked = rank_hospitals(hospitales_raw)

    return EstimateResponse(
        especialidad_sugerida=especialidad,
        patient=result.get("patient"),
        monto_copago=result.get("monto_copago"),
        copago_info=result.get("copay_info"),
        hospitales=hospitales_ranked,
    )
