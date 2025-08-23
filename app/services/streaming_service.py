import numpy as np
import structlog
import webrtcvad
from typing import AsyncGenerator
from .adapters.base import BaseSTTAdapter

log = structlog.get_logger(__name__)

class AudioProcessor:
    def __init__(self, adapter: BaseSTTAdapter, language: str | None = None, vad_aggressiveness: int = 3):
        self.adapter = adapter
        self.language = language if language else None
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.buffer = bytearray()
        # VAD 10, 20, 30 ms'lik frame'ler bekler. 16kHz, 16-bit mono için 30ms = 960 bytes
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

            # --- İŞTE NİHAİ DÜZELTME BURADA ---
            # Ham byte'ları, faster-whisper'ın doğrudan işleyebileceği bir float32 numpy array'ine dönüştür.
            # Bu, PyAV'ın dosya formatı algılama adımını atlamasını sağlar ve "Invalid Data" hatasını önler.
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0
            
            # Artık adaptörün transcribe metodu byte değil, numpy array almalı.
            # faster-whisper'ın kendi transcribe metodu bunu destekliyor, biz de doğrudan onu kullanalım.
            segments, info = self.adapter.model.transcribe(audio_np, language=self.language)
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

    async def transcribe_stream(self, audio_chunk_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        log.info("Starting audio stream transcription", language=self.language or "auto")
        
        async for chunk in audio_chunk_generator:
            self.buffer.extend(chunk)

            while len(self.buffer) >= self.vad_frame_size:
                frame = self.buffer[:self.vad_frame_size]
                self.buffer = self.buffer[self.vad_frame_size:]

                try:
                    # Ses verisinin 16000Hz, 16-bit mono PCM olduğu varsayılır.
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

        # Akış bittiğinde buffer'da kalan son veriyi de işle
        final_result = await self._process_final_chunk()
        if final_result:
            yield final_result