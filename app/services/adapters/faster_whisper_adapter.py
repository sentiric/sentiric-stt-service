from faster_whisper import WhisperModel
from app.core.config import settings
import structlog
import io
import numpy as np
from .base import BaseSTTAdapter
from typing import Optional, Union

log = structlog.get_logger(__name__)

# --- GÜVEN EŞİKLERİ (Yapılandırılabilir olabilir) ---
# Ortalama log olasılığı bu değerden düşük olan segmentleri atla.
# -1.0 çok gevşek, -0.5 daha sıkı bir filtredir.
LOGPROB_THRESHOLD = -0.6

# Konuşma olmama olasılığı bu değerden yüksek olan segmentleri atla.
# 0.90, %90 ihtimalle konuşma değil demek.
NO_SPEECH_PROB_THRESHOLD = 0.75

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

        # --- YENİ ve DOĞRU YÖNTEM: Olasılıkları alarak transkripsiyon yap ---
        segments, info = self.model.transcribe(
            input_for_model, 
            beam_size=5, 
            language=effective_language,
            vad_filter=True, # Whisper'ın kendi VAD'ını kullanalım
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        
        log.info(
            "Transcription by model completed",
            detected_language=info.language,
            language_probability=round(info.language_probability, 2)
        )

        filtered_segments = []
        for segment in segments:
            # Segmentin güvenilir olup olmadığını kontrol et
            is_reliable = (segment.avg_logprob > LOGPROB_THRESHOLD) and (segment.no_speech_prob < NO_SPEECH_PROB_THRESHOLD)
            
            if is_reliable:
                filtered_segments.append(segment.text)
                log.debug(
                    "Segment kept.", 
                    text=segment.text,
                    avg_logprob=round(segment.avg_logprob, 2),
                    no_speech_prob=round(segment.no_speech_prob, 2)
                )
            else:
                log.warn(
                    "Segment REJECTED due to low confidence.",
                    text=segment.text,
                    avg_logprob=round(segment.avg_logprob, 2),
                    no_speech_prob=round(segment.no_speech_prob, 2)
                )

        full_text = "".join(filtered_segments).strip()
        
        return full_text