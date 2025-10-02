from faster_whisper import WhisperModel
from app.core.config import settings
import structlog
import io
import numpy as np
from .base import BaseSTTAdapter
from typing import Optional, Union

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
            log.info("FasterWhisperAdapter model loaded successfully.")
        except Exception as e:
            self.model_loaded = False
            log.error("Failed to load FasterWhisperAdapter model", error=str(e), exc_info=True)
            raise e
    
    def transcribe(
        self, 
        audio_input: Union[bytes, np.ndarray], 
        language: Optional[str] = None,
        logprob_threshold: Optional[float] = None,
        no_speech_threshold: Optional[float] = None
    ) -> str:
        if not self.model_loaded or self.model is None:
            log.error("Transcription requested but model is not available.")
            raise RuntimeError("Model is not available for transcription.")
            
        effective_language = language if language else None
        
        if isinstance(audio_input, bytes):
            input_for_model = io.BytesIO(audio_input)
        elif isinstance(audio_input, np.ndarray):
            input_for_model = audio_input
        else:
            raise TypeError("Unsupported audio input type. Must be bytes or numpy.ndarray.")

        final_logprob_threshold = logprob_threshold if logprob_threshold is not None else settings.STT_SERVICE_LOGPROB_THRESHOLD
        final_no_speech_threshold = no_speech_threshold if no_speech_threshold is not None else settings.STT_SERVICE_NO_SPEECH_THRESHOLD
        
        log.debug(
            "Applying transcription filters",
            logprob_threshold=final_logprob_threshold,
            no_speech_threshold=final_no_speech_threshold
        )
        
        segments, info = self.model.transcribe(
            input_for_model, 
            beam_size=5, 
            language=effective_language
        )
        
        log.debug(
            "Transcription by model completed",
            detected_language=info.language,
            language_probability=round(info.language_probability, 2)
        )

        filtered_segments = []
        rejected_texts = [] # Reddedilenleri loglamak için bir liste
        for segment in segments:
            is_reliable = (
                segment.avg_logprob > final_logprob_threshold and 
                segment.no_speech_prob < final_no_speech_threshold
            )
            
            if is_reliable:
                filtered_segments.append(segment.text)
            else:
                rejected_texts.append(segment.text.strip())

        # Eğer herhangi bir segment reddedildiyse, bunu tek bir logda toplayalım
        if rejected_texts:
            log.warn(
                "Segments REJECTED due to low confidence.",
                rejected_count=len(rejected_texts),
                rejected_texts=rejected_texts,
                logprob_threshold=final_logprob_threshold,
                no_speech_threshold=final_no_speech_threshold
            )
        
        # Sadece kabul edilen segmentleri birleştir
        full_text = "".join(filtered_segments).strip()
        
        return full_text