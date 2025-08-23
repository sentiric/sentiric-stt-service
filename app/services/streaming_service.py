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
        self.vad_frame_size = 960
        self.speech_frames = bytearray()
        self.is_speaking = False
        self.silent_chunks = 0
        # Konuşma olarak kabul edilecek minimum frame sayısı. (örn, ~150ms)
        self.min_speech_frames = 5 

    async def _process_final_chunk(self):
        # Eğer birikmiş konuşma çok kısaysa, bunu gürültü olarak kabul et ve atla.
        if len(self.speech_frames) < self.vad_frame_size * self.min_speech_frames:
            self.speech_frames.clear()
            return None
        
        try:
            audio_data = bytes(self.speech_frames)
            self.speech_frames.clear()
            
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0
            final_text = self.adapter.transcribe(audio_np, self.language)

            if final_text:
                log.info("Final transcription segment generated", text_length=len(final_text))
                return {"type": "final", "text": final_text}
                
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
                    is_speech = self.vad.is_speech(frame, 16000)
                except Exception:
                    is_speech = False

                if is_speech:
                    self.speech_frames.extend(frame)
                    self.is_speaking = True
                    self.silent_chunks = 0
                elif self.is_speaking:
                    # Konuşma bittiğinde sessizlik saymaya başla
                    self.silent_chunks += 1
                    # ~750ms'lik bir sessizlikten sonra transkripsiyonu tetikle
                    if self.silent_chunks > 25:
                        final_result = await self._process_final_chunk()
                        if final_result:
                            yield final_result
                        self.is_speaking = False
                        self.silent_chunks = 0

        # Akış bittiğinde son parçayı da işle
        final_result = await self._process_final_chunk()
        if final_result:
            yield final_result