"""
Application settings loaded from environment variables.
Pydantic BaseSettings handles validation and defaults.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_env: str = "development"
    secret_key: str = "dev-secret"

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "neuro_health_db"

    # Model
    model_path: str = "ai/model/brain_tumor_cnn.h5"
    image_size: int = 128

    # Resource pool defaults
    total_icu_beds: int = 10
    total_doctors: int = 5
    total_ot_rooms: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance (singleton)."""
    return Settings()
