from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sentiric STT Service"
    API_V1_STR: str = "/api/v1"
    ENV: str = "production"
    LOG_LEVEL: str = "INFO"

    # --- ADAPTÖR SEÇİMİ ---
    STT_ADAPTER: str = "faster_whisper" # Gelecekte 'whisper_cpp' olabilir

    # --- FASTER-WHISPER AYARLARI ---
    STT_MODEL_SIZE: str = "base"
    STT_DEVICE: str = "cpu"
    STT_COMPUTE_TYPE: str = "int8"

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()