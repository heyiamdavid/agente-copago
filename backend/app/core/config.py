"""Variables de entorno (Groq, Notion, etc.)."""
from typing import Union
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    notion_token: str = ""
    # Bases de datos Notion (el usuario las configura)
    notion_db_patients: str = ""       # DB de pacientes / planes
    notion_db_hospitals: str = ""      # DB de red hospitalaria
    notion_db_copay: str = ""          # DB de tabla de copagos
    # Modelo Groq a usar (cambiamos a un modelo más rápido y con mayor límite gratuito)
    groq_model: str = "llama-3.1-8b-instant"
    # CORS (Separados por comas en el .env)
    cors_origins: Union[str, list[str]] = [
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://app.agno.com",
        "https://os.agno.com"
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
