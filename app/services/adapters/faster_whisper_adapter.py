from faster_whisper import WhisperModel
from app.core.config import settings
import structlog
import io
from .base import BaseSTTAdapter
from typing import Optional

log = structlog.get_logger(__name__)

class FasterWhisperAdapter(BaseSTTAdapter):
    _model: WhisperModel = None
    
    def __init__(self):
        if FasterWhisperAdapter._model is None:
            log.info(
                "Loading FasterWhisperAdapter model...",
                model=settings.STT_SERVICE_MODEL_SIZE,
                device=settings.STT_SERVICE_DEVICE,
                compute_type=settings.STT_SERVICE_COMPUTE_TYPE
            )
            try:
                FasterWhisperAdapter._model = WhisperModel(
                    settings.STT_SERVICE_MODEL_SIZE,
                    device=settings.STT_SERVICE_DEVICE,
                    compute_type=settings.STT_SERVICE_COMPUTE_TYPE
                )
                log.info("FasterWhisperAdapter model loaded successfully.")
            except Exception as e:
                log.error("Failed to load FasterWhisperAdapter model", error=str(e), exc_info=True)
                raise e

    def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        # --- YENİ DÜZELTME: Gelen dil parametresini temizle ---
        # Eğer UI'dan veya API'den boş bir string gelirse, bunu 'None' olarak ayarla
        # ki faster-whisper otomatik dil tespiti yapabilsin.
        effective_language = language if language else None
        
        audio_stream = io.BytesIO(audio_bytes)
        
        segments, info = self._model.transcribe(
            audio_stream, 
            beam_size=5, 
            language=effective_language # Temizlenmiş parametreyi kullan
        )
        
        log.info(
            "Transcription completed",
            detected_language=info.language,
            language_probability=round(info.language_probability, 2),
            requested_language=language or "auto"
        )

        full_text = "".join(segment.text for segment in segments)
        return full_text.strip()