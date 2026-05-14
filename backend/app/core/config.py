"""Variables de entorno (Groq, Notion, etc.)."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    notion_token: str = ""
    # Bases de datos Notion (el usuario las configura)
    notion_db_patients: str = ""       # DB de pacientes / planes
    notion_db_hospitals: str = ""      # DB de red hospitalaria
    notion_db_copay: str = ""          # DB de tabla de copagos
    # Modelo Groq a usar
    groq_model: str = "llama-3.3-70b-versatile"
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
