from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sentiric STT Service"
    API_V1_STR: str = "/api/v1"
    ENV: str = "production"
    LOG_LEVEL: str = "INFO"
    
    STT_MODEL_NAME: str = "openai/whisper-base"
    STT_MODEL_DEVICE: str = "cpu" # veya "cuda"

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

settings = Settings()