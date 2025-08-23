from faster_whisper import WhisperModel
from app.core.config import settings
import structlog
import io
from .base import BaseSTTAdapter
from typing import Optional

log = structlog.get_logger(__name__)

class FasterWhisperAdapter(BaseSTTAdapter):
    
    def __init__(self):
        self.model: WhisperModel | None = None
        self.model_loaded: bool = False
        log.info(
            "Initializing FasterWhisperAdapter and loading model...",
            model=settings.STT_SERVICE_MODEL_SIZE,
            device=settings.STT_SERVICE_DEVICE,
            compute_type=settings.STT_SERVICE_COMPUTE_TYPE
        )
        try:
            self.model = WhisperModel(
                settings.STT_SERVICE_MODEL_SIZE,
                device=settings.STT_SERVICE_DEVICE,
                compute_type=settings.STT_SERVICE_COMPUTE_TYPE
            )
            self.model_loaded = True
            log.info("FasterWhisperAdapter model loaded successfully into instance.")
        except Exception as e:
            self.model_loaded = False
            log.error("Failed to load FasterWhisperAdapter model", error=str(e), exc_info=True)
            # Yükleme başarısız olsa bile uygulamanın çökmemesi için hatayı yutmuyoruz, 
            # ancak `stt_service.py`'deki try-except bloğu bunu yakalayacak.
            raise e

    def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        if not self.model_loaded or self.model is None:
            log.error("Transcription called but model is not loaded.")
            raise RuntimeError("Model is not available for transcription.")
            
        effective_language = language if language else None
        
        audio_stream = io.BytesIO(audio_bytes)
        
        segments, info = self.model.transcribe(
            audio_stream, 
            beam_size=5, 
            language=effective_language
        )
        
        log.info(
            "Transcription completed",
            detected_language=info.language,
            language_probability=round(info.language_probability, 2),
            requested_language=language or "auto"
        )

        full_text = "".join(segment.text for segment in segments)
        return full_text.strip()