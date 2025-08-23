import asyncio
import numpy as np
import structlog
import webrtcvad
from typing import AsyncGenerator

from app.services.stt_service import get_adapter

log = structlog.get_logger(__name__)

class AudioProcessor:
    def __init__(self, language: str | None = None, vad_aggressiveness: int = 3):
        self.adapter = get_adapter()
        if not self.adapter:
            raise RuntimeError("STT adapter is not loaded.")
        
        self.language = language if language else None
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.buffer = bytearray()
        # VAD 10, 20, 30 ms'lik frame'ler bekler. 30ms = 16kHz * 16-bit (2 byte) * 0.030s = 960 bytes
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
            
            # Gelen ses byte'larını numpy array'e çevir. Sesin 16-bit PCM formatında olduğu varsayılır.
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            segments, info = self.adapter._model.transcribe(audio_np, language=self.language, without_timestamps=True)
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
                    "language_probability": info.language_probability
                }
        except Exception as e:
            log.error("Error during final transcription chunk processing", error=str(e), exc_info=True)
            return {"type": "error", "message": str(e)}
        return None


    async def transcribe_stream(self, audio_chunk_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        log.info("Starting audio stream transcription", language=self.language or "auto")
        
        async for chunk in audio_chunk_generator:
            self.buffer.extend(chunk)

            while len(self.buffer) >= self.vad_frame_size:
                frame = self.buffer[:self.vad_frame_size]
                self.buffer = self.buffer[self.vad_frame_size:]

                is_speech = self.vad.is_speech(frame, 16000)

                if is_speech:
                    self.speech_frames.extend(frame)
                    self.is_speaking = True
                    self.silent_chunks = 0
                elif self.is_speaking:
                    # Konuşma bitti ve sessizlik başladı
                    self.silent_chunks += 1
                    # Yaklaşık 0.5 saniyelik bir sessizlikten sonra transkripsiyonu tetikle
                    if self.silent_chunks > 15:
                        final_result = await self._process_final_chunk()
                        if final_result:
                            yield final_result
                        self.is_speaking = False
                        self.silent_chunks = 0

        # Akış bittiğinde buffer'da kalan son veriyi de işle
        final_result = await self._process_final_chunk()
        if final_result:
            yield final_result