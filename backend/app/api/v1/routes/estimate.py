"""Estimación explícita de copago / hospital en red."""
from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def estimate():
    # TODO: cruzar plan + red hospitalaria (Notion u otra fuente)
    return {"copay": None, "suggested_hospital": None}
