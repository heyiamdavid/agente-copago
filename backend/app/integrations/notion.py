"""Cliente Notion: planes, red hospitalaria, tablas de copago.

El usuario configura las bases de datos de Notion.
Este módulo consume la API REST de Notion y expone helpers
tipados para el resto de la app.

Estructura esperada por DB:
──────────────────────────────────────────────────────────────
NOTION_DB_PATIENTS   (tabla de pacientes / planes de seguro)
  Columns: patient_id (title), nombre, plan_id, plan_nombre,
           deducible_anual, deducible_cubierto, copago_base (%)

NOTION_DB_HOSPITALS  (red hospitalaria)
  Columns: hospital_id (title), nombre, ciudad, especialidades
           (multi-select), nivel (select: A/B/C), en_red (checkbox)

NOTION_DB_COPAY      (tabla de copagos por plan × especialidad)
  Columns: plan_id (title), especialidad, copago_fijo,
           copago_porcentaje, tope_bolsillo
──────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.notion_token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


async def _query_database(db_id: str, filter_body: dict | None = None) -> list[dict[str, Any]]:
    """Consulta una base de datos Notion y retorna los resultados."""
    if not db_id:
        logger.warning("Notion DB ID not configured; returning empty list.")
        return []

    url = f"{NOTION_API_BASE}/databases/{db_id}/query"
    body: dict[str, Any] = {}
    if filter_body:
        body["filter"] = filter_body

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(url, headers=_headers(), json=body)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])


def _text_prop(page: dict, key: str) -> str:
    """Extrae el valor de texto de una propiedad Notion."""
    props = page.get("properties", {})
    prop = props.get(key, {})
    ptype = prop.get("type", "")
    if ptype == "title":
        items = prop.get("title", [])
    elif ptype == "rich_text":
        items = prop.get("rich_text", [])
    else:
        return ""
    return "".join(t.get("plain_text", "") for t in items)


def _number_prop(page: dict, key: str) -> float | None:
    props = page.get("properties", {})
    prop = props.get(key, {})
    return prop.get("number")


def _select_prop(page: dict, key: str) -> str:
    props = page.get("properties", {})
    sel = props.get(key, {}).get("select") or {}
    return sel.get("name", "")


def _multi_select_prop(page: dict, key: str) -> list[str]:
    props = page.get("properties", {})
    items = props.get(key, {}).get("multi_select", [])
    return [i.get("name", "") for i in items]


def _checkbox_prop(page: dict, key: str) -> bool:
    props = page.get("properties", {})
    return bool(props.get(key, {}).get("checkbox", False))


# ── Public helpers ────────────────────────────────────────────────────────────

async def get_patient_plan(patient_id: str) -> dict | None:
    """Devuelve el plan de seguro del paciente dado su ID."""
    rows = await _query_database(
        settings.notion_db_patients,
        filter_body={
            "property": "PatientID",
            "rich_text": {"equals": patient_id},
        },
    )
    if not rows:
        return None
    p = rows[0]
    return {
        "patient_id": _text_prop(p, "PatientID"),
        "nombre": _text_prop(p, "Nombre 1"),
        "plan_nombre": _text_prop(p, "Plan 1"),  # Notion Relation / Text
        "deducible_anual": _number_prop(p, "Deducible Anual"),
        "deducible_cubierto": _number_prop(p, "Deducible Cubierto"),
        "copago_base": 0, # Se obtiene de la tabla de copagos
    }


async def create_patient_in_notion(patient_id: str, nombre: str, plan_nombre: str) -> dict | None:
    """Crea una nueva fila en la base de datos de pacientes de Notion."""
    if not settings.notion_db_patients:
        logger.warning("Notion DB ID not configured; cannot create patient.")
        return None

    url = f"{NOTION_API_BASE}/pages"
    body = {
        "parent": {"database_id": settings.notion_db_patients},
        "properties": {
            "Nombre 1": {"title": [{"text": {"content": nombre}}]},
            "PatientID": {"rich_text": [{"text": {"content": patient_id}}]},
            "Plan 1": {"rich_text": [{"text": {"content": plan_nombre}}]},
            "Deducible Anual": {"number": 0},
            "Deducible Cubierto": {"number": 0},
        }
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            resp = await client.post(url, headers=_headers(), json=body)
            resp.raise_for_status()
            logger.info(f"Paciente {patient_id} registrado exitosamente en Notion.")
            return await get_patient_plan(patient_id)
        except Exception as e:
            logger.error(f"Error creando paciente en Notion: {e}")
            return None


async def get_copay_for_plan(plan_id: str, especialidad: str) -> dict | None:
    """Retorna el copago configurado para un plan + especialidad."""
    rows = await _query_database(
        settings.notion_db_copay,
        filter_body={
            "and": [
                {"property": "Plan", "title": {"equals": plan_id}},
                {"property": "Especialidad", "select": {"equals": especialidad}},
            ]
        },
    )
    if not rows:
        # Fallback si Especialidad no es select sino rich_text
        rows = await _query_database(
            settings.notion_db_copay,
            filter_body={
                "and": [
                    {"property": "Plan", "title": {"equals": plan_id}},
                    {"property": "Especialidad", "rich_text": {"equals": especialidad}},
                ]
            },
        )

    if not rows:
        return None
    r = rows[0]
    return {
        "plan_id": _text_prop(r, "Plan"),
        "especialidad": _text_prop(r, "Especialidad") or _select_prop(r, "Especialidad"),
        "copago_fijo": _number_prop(r, "Copago Fijo"),
        "copago_porcentaje": _number_prop(r, "Cobertura %"),
        "requiere_referencia": _checkbox_prop(r, "Requiere Referencia"),
    }


async def get_hospitals_by_specialty(especialidad: str) -> list[dict]:
    """Lista hospitales en red que atienden la especialidad dada."""
    rows = await _query_database(
        settings.notion_db_hospitals,
        filter_body={
            "and": [
                {
                    "property": "especialidades",
                    "multi_select": {"contains": especialidad},
                },
                {"property": "en_red", "checkbox": {"equals": True}},
            ]
        },
    )
    hospitals = []
    for r in rows:
        hospitals.append(
            {
                "hospital_id": _text_prop(r, "Nombre"),
                "nombre": _text_prop(r, "Nombre"),
                "ciudad": _select_prop(r, "Ciudad"),
                "direccion": _text_prop(r, "Dirección"),
                "nivel": _select_prop(r, "Nivel"),
                "especialidades": _multi_select_prop(r, "Especialidades"),
                "en_red": _checkbox_prop(r, "En Red"),
                "latitud": _number_prop(r, "Latitud"),
                "longitud": _number_prop(r, "Longitud"),
            }
        )
    return hospitals
