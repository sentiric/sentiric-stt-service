import numpy as np
import structlog
import webrtcvad
from typing import AsyncGenerator
from .adapters.base import BaseSTTAdapter

log = structlog.get_logger(__name__)

# Whisper'ın anlamsız veya tekrar eden token'larını bastırmak için.
# Bu token ID'leri, modelin sessizlik veya gürültü durumunda ürettiği jenerik metinleri engeller.
SUPPRESS_TOKENS = [-1, 32331, 41558, 2691, 322, 50257]

class AudioProcessor:
    def __init__(self, adapter: BaseSTTAdapter, language: str | None = None, vad_aggressiveness: int = 3):
        self.adapter = adapter
        self.language = language if language else None
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.buffer = bytearray()
        self.vad_frame_size = 960
        self.speech_frames = bytearray()
        self.is_speaking = False
        self.silent_chunks = 0

    async def _process_final_chunk(self):
        """Buffer'da kalan son ses parçasını işler ve nihai transkripti döndürür."""
        if not self.speech_frames:
            return None
        
        try:
            audio_data = bytes(self.speech_frames)
            self.speech_frames.clear()

            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0
            
            # --- YENİ AI AYARLARI ---
            segments, info = self.adapter.model.transcribe(
                audio_np, 
                language=self.language,
                # no_speech_threshold: Eğer sesin konuşma olma ihtimali bu değerden düşükse, boş metin döndür.
                # Bu, gürültünün metne çevrilmesini engeller.
                no_speech_threshold=0.6,
                # log_prob_threshold: Ortalama log olasılığı bu değerin altındaysa, segmentleri atla.
                # Bu, yüksek derecede anlamsız veya halüsinasyon içeren çıktıları filtreler.
                log_prob_threshold=-1.0,
                # suppress_tokens: Belirtilen token'ların çıktıda görünmesini engelle.
                suppress_tokens=SUPPRESS_TOKENS
            )
            final_text = "".join(s.text for s in segments).strip()

            if final_text:
                log.info(
                    "Final transcription segment generated",
                    text_length=len(final_text),
                    detected_language=info.language,
                    lang_probability=round(info.language_probability, 2)
                )
                return {
                    "type": "final",
                    "text": final_text,
                    "language": info.language,
                    "language_probability": info.language_probability,
                }
        except Exception as e:
            log.error("Error during final transcription chunk processing", error=str(e), exc_info=True)
            return {"type": "error", "message": "Transcription processing error."}
        return None

    # ... transcribe_stream metodu aynı kalıyor ...
    async def transcribe_stream(self, audio_chunk_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        log.info("Starting audio stream transcription", language=self.language or "auto")
        
        async for chunk in audio_chunk_generator:
            self.buffer.extend(chunk)

            while len(self.buffer) >= self.vad_frame_size:
                frame = self.buffer[:self.vad_frame_size]
                self.buffer = self.buffer[self.vad_frame_size:]

                try:
                    is_speech = self.vad.is_speech(frame, 16000)
                except Exception:
                    is_speech = False

                if is_speech:
                    self.speech_frames.extend(frame)
                    self.is_speaking = True
                    self.silent_chunks = 0
                elif self.is_speaking:
                    self.silent_chunks += 1
                    if self.silent_chunks > 15: # ~0.5s sessizlik
                        final_result = await self._process_final_chunk()
                        if final_result:
                            yield final_result
                        self.is_speaking = False
                        self.silent_chunks = 0

        final_result = await self._process_final_chunk()
        if final_result:
            yield final_result