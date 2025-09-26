# sentiric-stt-service/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sentiric STT Service"
    API_V1_STR: str = "/api/v1"
    ENV: str = "production"
    LOG_LEVEL: str = "INFO"

    SERVICE_VERSION: str = Field("0.0.0", validation_alias="SERVICE_VERSION")
    GIT_COMMIT: str = Field("unknown", validation_alias="GIT_COMMIT")
    BUILD_DATE: str = Field("unknown", validation_alias="BUILD_DATE")

    STT_SERVICE_ADAPTER: str = Field("faster_whisper", validation_alias="STT_SERVICE_ADAPTER")
    STT_SERVICE_MODEL_SIZE: str = Field("base", validation_alias="STT_SERVICE_MODEL_SIZE")
    STT_SERVICE_DEVICE: str = Field("cpu", validation_alias="STT_SERVICE_DEVICE")
    STT_SERVICE_COMPUTE_TYPE: str = Field("int8", validation_alias="STT_SERVICE_COMPUTE_TYPE")
    STT_SERVICE_TARGET_SAMPLE_RATE: int = Field(16000, validation_alias="STT_SERVICE_TARGET_SAMPLE_RATE")
    STT_SERVICE_LOGPROB_THRESHOLD: float = Field(-1.0, validation_alias="STT_SERVICE_LOGPROB_THRESHOLD")
    STT_SERVICE_NO_SPEECH_THRESHOLD: float = Field(0.75, validation_alias="STT_SERVICE_NO_SPEECH_THRESHOLD")
    
    # --- YENİ VAD AYARI ---
    # Modelin bir konuşma segmentini sonlandırmadan önce beklemesi gereken minimum sessizlik süresi (milisaniye).
    # Telefon görüşmelerindeki doğal duraksamalar için bu değeri artırmak faydalıdır.
    STT_SERVICE_VAD_MIN_SILENCE_MS: int = Field(1000, validation_alias="STT_SERVICE_VAD_MIN_SILENCE_MS")
    # --- YENİ AYAR SONU ---
    
    model_config = SettingsConfigDict(
        extra='ignore',
        case_sensitive=False
    )

settings = Settings()