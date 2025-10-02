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

    # --- STT Adapter Settings ---
    STT_SERVICE_ADAPTER: str = Field("faster_whisper", validation_alias="STT_SERVICE_ADAPTER")
    STT_SERVICE_MODEL_SIZE: str = Field("medium", validation_alias="STT_SERVICE_MODEL_SIZE")
    STT_SERVICE_DEVICE: str = Field("cpu", validation_alias="STT_SERVICE_DEVICE")
    STT_SERVICE_COMPUTE_TYPE: str = Field("int8", validation_alias="STT_SERVICE_COMPUTE_TYPE")
    STT_SERVICE_TARGET_SAMPLE_RATE: int = Field(16000, validation_alias="STT_SERVICE_TARGET_SAMPLE_RATE")

    # --- Whisper Filtering Settings ---
    STT_SERVICE_LOGPROB_THRESHOLD: float = Field(-1.0, validation_alias="STT_SERVICE_LOGPROB_THRESHOLD")
    STT_SERVICE_NO_SPEECH_THRESHOLD: float = Field(0.75, validation_alias="STT_SERVICE_NO_SPEECH_THRESHOLD")
    
    # --- VAD (Voice Activity Detection) Settings ---
    # VAD'ın ne kadar agresif olacağını belirler (0-3 arası). 3 en agresif olanıdır.
    STT_SERVICE_VAD_AGGRESSIVENESS: int = Field(3, validation_alias="STT_SERVICE_VAD_AGGRESSIVENESS")
    # VAD'ın bir cümlenin bittiğini kabul etmesi için gereken minimum sessizlik süresi (ms).
    STT_SERVICE_VAD_END_OF_SPEECH_MS: int = Field(700, validation_alias="STT_SERVICE_VAD_END_OF_SPEECH_MS")
    # İşleme alınacak minimum konuşma süresi (ms). Bundan kısa sesler gürültü kabul edilir.
    STT_SERVICE_VAD_MIN_SPEECH_MS: int = Field(250, validation_alias="STT_SERVICE_VAD_MIN_SPEECH_MS")
    # VAD'ın daha uzun sessizliklerde tetikte kalmasını sağlayan periyodik kontrol süresi (ms).
    STT_SERVICE_VAD_PADDING_MS: int = Field(300, validation_alias="STT_SERVICE_VAD_PADDING_MS")

    model_config = SettingsConfigDict(
        extra='ignore',
        case_sensitive=False
    )

settings = Settings()