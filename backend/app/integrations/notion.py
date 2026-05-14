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
            "property": "patient_id",
            "title": {"equals": patient_id},
        },
    )
    if not rows:
        return None
    p = rows[0]
    return {
        "patient_id": _text_prop(p, "patient_id"),
        "nombre": _text_prop(p, "nombre"),
        "plan_id": _text_prop(p, "plan_id"),
        "plan_nombre": _text_prop(p, "plan_nombre"),
        "deducible_anual": _number_prop(p, "deducible_anual"),
        "deducible_cubierto": _number_prop(p, "deducible_cubierto"),
        "copago_base": _number_prop(p, "copago_base"),
    }


async def get_copay_for_plan(plan_id: str, especialidad: str) -> dict | None:
    """Retorna el copago configurado para un plan + especialidad."""
    rows = await _query_database(
        settings.notion_db_copay,
        filter_body={
            "and": [
                {"property": "plan_id", "title": {"equals": plan_id}},
                {"property": "especialidad", "rich_text": {"equals": especialidad}},
            ]
        },
    )
    if not rows:
        return None
    r = rows[0]
    return {
        "plan_id": _text_prop(r, "plan_id"),
        "especialidad": _text_prop(r, "especialidad"),
        "copago_fijo": _number_prop(r, "copago_fijo"),
        "copago_porcentaje": _number_prop(r, "copago_porcentaje"),
        "tope_bolsillo": _number_prop(r, "tope_bolsillo"),
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
                "hospital_id": _text_prop(r, "hospital_id"),
                "nombre": _text_prop(r, "nombre"),
                "ciudad": _text_prop(r, "ciudad"),
                "nivel": _select_prop(r, "nivel"),
                "especialidades": _multi_select_prop(r, "especialidades"),
                "en_red": _checkbox_prop(r, "en_red"),
            }
        )
    return hospitals
