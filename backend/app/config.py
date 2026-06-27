"""
Centralized application settings.

All configuration is loaded from environment variables (via a .env file
in development). Nothing here should ever contain a hardcoded secret.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Groq (free, OpenAI-compatible chat completions API) ---
    groq_api_key: str
    groq_chat_model: str = "llama-3.3-70b-versatile"
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # --- Local embeddings (fastembed/ONNX, no API key, no torch dependency) ---
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"

    # --- CORS ---
    allowed_origins: str = "http://localhost:3000"

    # --- External APIs (no keys required for these) ---
    noaa_application_name: str = "OceanGPT"
    obis_base_url: str = "https://api.obis.org/v3"
    worms_base_url: str = "https://www.marinespecies.org/rest"
    noaa_coops_base_url: str = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    noaa_mdapi_base_url: str = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations"
    open_meteo_marine_base_url: str = "https://marine-api.open-meteo.com/v1/marine"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

