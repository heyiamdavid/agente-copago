"""Variables de entorno (Groq, Notion, etc.)."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    notion_token: str = ""
    notion_database_id: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
