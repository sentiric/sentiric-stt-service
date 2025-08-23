from faster_whisper import WhisperModel
from app.core.config import settings
import structlog
import io
import numpy as np
from .base import BaseSTTAdapter
from typing import Optional, Union

log = structlog.get_logger(__name__)

SUPPRESS_TOKENS = [-1]

class FasterWhisperAdapter(BaseSTTAdapter):
    
    def __init__(self):
        # ... __init__ kodu aynı ...
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
            raise e

    def transcribe(self, audio_input: Union[bytes, np.ndarray], language: Optional[str] = None) -> str:
        if not self.model_loaded or self.model is None:
            raise RuntimeError("Model is not available for transcription.")
            
        effective_language = language if language else None
        
        if isinstance(audio_input, bytes):
            input_for_model = io.BytesIO(audio_input)
        elif isinstance(audio_input, np.ndarray):
            input_for_model = audio_input
        else:
            raise TypeError("Unsupported audio input type. Must be bytes or numpy.ndarray.")

        segments, info = self.model.transcribe(
            input_for_model, 
            beam_size=5, 
            language=effective_language,
            # --- YENİ STRATEJİ ---
            # Whisper'ın kendi VAD filtresini etkinleştir. Bu, gürültülü segmentleri atar.
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        log.info(
            "Transcription completed",
            detected_language=info.language,
            language_probability=round(info.language_probability, 2),
            requested_language=language or "auto"
        )

        full_text = "".join(segment.text for segment in segments)
        return full_text.strip()