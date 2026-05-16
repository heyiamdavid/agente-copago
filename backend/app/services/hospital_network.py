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


import math

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia en km entre dos puntos geográficos."""
    R = 6371  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


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


def rank_hospitals(
    hospitales: list[dict], 
    user_lat: float | None = None, 
    user_lon: float | None = None
) -> list[dict]:
    """
    Ordena hospitales por cercanía (si hay ubicación) y luego por nivel.
    """
    level_order = {"Alta Complejidad": 0, "Especializado": 1, "Básico": 2}
    
    for h in hospitales:
        h_lat = h.get("latitud")
        h_lon = h.get("longitud")
        if user_lat and user_lon and h_lat and h_lon:
            h["distancia_km"] = round(haversine(user_lat, user_lon, h_lat, h_lon), 2)
        else:
            h["distancia_km"] = None

    # Ordenar: primero los que tienen distancia (más cercanos), luego por nivel
    return sorted(
        hospitales, 
        key=lambda h: (
            h["distancia_km"] if h["distancia_km"] is not None else 9999,
            level_order.get(h.get("nivel"), 99)
        )
    )
