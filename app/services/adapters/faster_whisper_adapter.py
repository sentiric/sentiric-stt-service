# app/services/adapters/faster_whisper_adapter.py

from faster_whisper import WhisperModel
from app.core.config import settings
from app.core.logging import logger
import io
from .base import BaseSTTAdapter

class FasterWhisperAdapter(BaseSTTAdapter):
    """
    faster-whisper kütüphanesini kullanarak transkripsiyon yapan somut adaptör.
    """
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

    def transcribe(self, audio_bytes: bytes) -> str:
        audio_stream = io.BytesIO(audio_bytes)
        
        segments, info = self._model.transcribe(audio_stream, beam_size=5)
        
        logger.info(
            "Transkripsiyon tamamlandı.",
            language=info.language,
            language_probability=info.language_probability
        )

        full_text = "".join(segment.text for segment in segments)
        return full_text.strip()