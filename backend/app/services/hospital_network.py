"""Red de hospitales, especialidades, costos relativos."""
from __future__ import annotations

from app.integrations.notion import get_hospitals_by_specialty


# Mapa estático de síntomas → especialidad (respaldo cuando el LLM no está disponible)
SYMPTOM_SPECIALTY_MAP: dict[str, str] = {
    "dolor de cabeza": "Neurología",
    "migraña": "Neurología",
    "dolor de pecho": "Cardiología",
    "corazón": "Cardiología",
    "tos": "Medicina General",
    "fiebre": "Medicina General",
    "gripe": "Medicina General",
    "resfriado": "Medicina General",
    "dolor de estómago": "Gastroenterología",
    "náuseas": "Gastroenterología",
    "vómitos": "Gastroenterología",
    "dolor de rodilla": "Traumatología",
    "fractura": "Traumatología",
    "hueso": "Traumatología",
    "vista": "Oftalmología",
    "ojo": "Oftalmología",
    "oído": "Otorrinolaringología",
    "garganta": "Otorrinolaringología",
    "piel": "Dermatología",
    "sarpullido": "Dermatología",
    "embarazo": "Ginecología",
    "menstruación": "Ginecología",
    "niño": "Pediatría",
    "bebé": "Pediatría",
    "depresión": "Psiquiatría",
    "ansiedad": "Psiquiatría",
    "dientes": "Odontología",
    "muela": "Odontología",
    "riñón": "Urología",
    "orina": "Urología",
    "pulmón": "Neumología",
    "respiración": "Neumología",
    "diabetes": "Endocrinología",
    "tiroides": "Endocrinología",
}


def guess_specialty_from_symptom(symptom: str) -> str | None:
    """Heurística básica para mapear síntoma → especialidad (fallback)."""
    symptom_lower = symptom.lower()
    for keyword, specialty in SYMPTOM_SPECIALTY_MAP.items():
        if keyword in symptom_lower:
            return specialty
    return None


async def get_network_hospitals(especialidad: str) -> list[dict]:
    """Devuelve la lista de hospitales en red para una especialidad."""
    return await get_hospitals_by_specialty(especialidad)


def rank_hospitals(hospitales: list[dict]) -> list[dict]:
    """
    Ordena hospitales por nivel (A > B > C) para recomendar
    el más conveniente económicamente para el paciente.
    """
    level_order = {"A": 0, "B": 1, "C": 2}
    return sorted(hospitales, key=lambda h: level_order.get(h.get("nivel", "C"), 99))
