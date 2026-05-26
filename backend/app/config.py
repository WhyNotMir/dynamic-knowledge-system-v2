from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        extra="ignore",
    )

    database_url: str

    redis_url: str
    upload_dir: str

    cors_allowed_origins: list[str]

    openai_api_key: str | None = None
    groq_api_key: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    qa_model: str = "llama-3.3-70b-versatile"

settings = Settings()
