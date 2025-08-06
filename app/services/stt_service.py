from transformers import pipeline
from functools import lru_cache
from app.core.config import settings
from app.core.logging import logger
import soundfile as sf
import io

@lru_cache(maxsize=1)
def load_stt_model():
    """
    Whisper modelini sadece bir kez yükler ve cache'ler.
    Bu fonksiyon uygulama başlangıcında çağrılır.
    """
    logger.info(f"STT modeli yükleniyor: {settings.STT_MODEL_NAME}", device=settings.STT_MODEL_DEVICE)
    
    # DÜZELTME: 'accelerate' kütüphanesi cihazı otomatik olarak
    # yöneteceğinden, 'device' argümanını kaldırıyoruz.
    pipe = pipeline(
        "automatic-speech-recognition",
        model=settings.STT_MODEL_NAME,
        model_kwargs={"load_in_8bit": True if settings.STT_MODEL_DEVICE == "cpu" else False}
    )
    logger.info("STT modeli başarıyla yüklendi.")
    return pipe

def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Verilen ses byte'larını metne çevirir.
    """
    stt_pipeline = load_stt_model()
    
    audio_data, samplerate = sf.read(io.BytesIO(audio_bytes))
    
    # Pipeline'a gönderirken de 'device' belirtmiyoruz.
    # Kütüphane, yükleme sırasında seçilen cihazı kullanacaktır.
    result = stt_pipeline({"sampling_rate": samplerate, "raw": audio_data})
    
    return result["text"]