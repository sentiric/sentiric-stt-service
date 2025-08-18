from faster_whisper import WhisperModel
from app.core.config import settings
from app.core.logging import logger
import io
from .base import BaseSTTAdapter
from typing import Optional

class FasterWhisperAdapter(BaseSTTAdapter):
    _model: WhisperModel = None
    
    def __init__(self):
        if FasterWhisperAdapter._model is None:
            logger.info(
                "FasterWhisperAdapter modeli yükleniyor...",
                model=settings.STT_MODEL_SIZE,
                device=settings.STT_DEVICE,
                compute_type=settings.STT_COMPUTE_TYPE
            )
            try:
                FasterWhisperAdapter._model = WhisperModel(
                    settings.STT_MODEL_SIZE,
                    device=settings.STT_DEVICE,
                    compute_type=settings.STT_COMPUTE_TYPE
                )
                logger.info("FasterWhisperAdapter modeli başarıyla yüklendi.")
            except Exception as e:
                logger.error("FasterWhisperAdapter modeli yüklenirken hata oluştu.", error=str(e))
                raise e

    # DÜZELTME: Fonksiyon artık opsiyonel bir 'language' parametresi alıyor.
    def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        audio_stream = io.BytesIO(audio_bytes)
        
        # DÜZELTME: Dil parametresini transcribe fonksiyonuna iletiyoruz.
        segments, info = self._model.transcribe(
            audio_stream, 
            beam_size=5, 
            language=language # Eğer None ise, otomatik tespit çalışır.
        )
        
        logger.info(
            "Transkripsiyon tamamlandı.",
            detected_language=info.language,
            language_probability=info.language_probability,
            requested_language=language
        )

        full_text = "".join(segment.text for segment in segments)
        return full_text.strip()