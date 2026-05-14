"""Punto de entrada FastAPI — Estimador Agéntico de Copago y Cobertura."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="Estimador Agéntico de Copago y Cobertura",
    description=(
        "API conversacional que ayuda al paciente a entender su cobertura "
        "de seguro antes de atenderse. Sugiere especialidad médica, calcula "
        "el copago y recomienda hospitales en red."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS para el frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health():
    """Verificación de estado del servidor."""
    return {"status": "ok", "service": "copay-estimator"}

# ── Integración con Agno AgentOS Dashboard ────────────────────────────────────
from agno.os import AgentOS
from app.agent.copay_agent import build_agent

agent_os = AgentOS(
    name="Copay Agent OS",
    agents=[build_agent()],
    base_app=app,
    cors_allowed_origins=settings.cors_origins,
)

# Reemplazamos app con la versión mejorada por AgentOS
app = agent_os.get_app()
