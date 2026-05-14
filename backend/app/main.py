"""Punto de entrada FastAPI (esqueleto)."""
from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(title="Estimador Agéntico de Copago y Cobertura")
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}
