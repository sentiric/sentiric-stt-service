from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Uygulamanın tüm yapılandırmasını ortam değişkenlerinden ve .env dosyasından
    yöneten merkezi sınıf. `validation_alias` kullanılarak, Python kodundaki
    alan adları ile .env dosyasındaki değişken adları eşleştirilir.
    """
    PROJECT_NAME: str = "Sentiric STT Service"
    API_V1_STR: str = "/api/v1"
    ENV: str = "production"
    LOG_LEVEL: str = "INFO"

    # --- ADAPTÖR SEÇİMİ ---
    # Kod içinde: settings.STT_SERVICE_ADAPTER
    # .env'de: STT_SERVICE_ADAPTER
    STT_SERVICE_ADAPTER: str = Field("faster_whisper", validation_alias="STT_SERVICE_ADAPTER")

    # --- FASTER-WHISPER AYARLARI ---
    # Kod içinde: settings.STT_SERVICE_MODEL_SIZE
    # .env'de: STT_SERVICE_MODEL_SIZE
    STT_SERVICE_MODEL_SIZE: str = Field("base", validation_alias="STT_SERVICE_MODEL_SIZE")
    
    # Kod içinde: settings.STT_SERVICE_DEVICE
    # .env'de: STT_SERVICE_DEVICE
    STT_SERVICE_DEVICE: str = Field("cpu", validation_alias="STT_SERVICE_DEVICE")
    
    # Kod içinde: settings.STT_SERVICE_COMPUTE_TYPE
    # .env'de: STT_SERVICE_COMPUTE_TYPE
    STT_SERVICE_COMPUTE_TYPE: str = Field("int8", validation_alias="STT_SERVICE_COMPUTE_TYPE")

    model_config = SettingsConfigDict(
        # Pydantic, değerleri doğrudan ortam değişkenlerinden okuyacak.
        # env_file=None, # Bu satırı tamamen silebiliriz, varsayılanı zaten budur
        extra='ignore',
        # Docker Compose'dan gelen büyük harfli değişkenleri okuyabilmek için
        # case_sensitive=False ayarı önemlidir.
        case_sensitive=False
    )

settings = Settings()