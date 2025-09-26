# sentiric-stt-service/app/services/streaming_service.py
import asyncio
import time
import numpy as np
import structlog
from typing import AsyncGenerator, Optional
from .adapters.base import BaseSTTAdapter

log = structlog.get_logger(__name__)

class AudioProcessor:
    def __init__(self,
                 adapter: BaseSTTAdapter,
                 language: str | None = None,
                 vad_aggressiveness: Optional[int] = None, # Bu parametre artık kullanılmayacak ama arayüz uyumluluğu için kalabilir
                 logprob_threshold: Optional[float] = None,
                 no_speech_threshold: Optional[float] = None):
        self.adapter = adapter
        self.language = language
        self.logprob_threshold = logprob_threshold
        self.no_speech_threshold = no_speech_threshold

        # vad_aggressiveness artık doğrudan kullanılmıyor, loglayabiliriz.
        if vad_aggressiveness is not None:
            log.debug("vad_aggressiveness parametresi alındı ancak FasterWhisper VAD tarafından doğrudan kullanılmıyor.", level=vad_aggressiveness)

        self.buffer = bytearray()
        self.bytes_per_ms = 32
        self.chunk_size = int(1.5 * 1000 * self.bytes_per_ms)
        self.min_chunk_size = int(0.5 * 1000 * self.bytes_per_ms)

        self.last_audio_time = time.time()
        self.no_speech_timeout_seconds = 10

    async def _process_chunk(self, audio_chunk: bytes):
        try:
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32767.0
            
            # --- ANA DÜZELTME BURADA ---
            # 'aggressiveness' parametresini VAD parametrelerinden kaldırıyoruz.
            # faster-whisper'ın dahili VAD'ı için önemli olan `min_silence_duration_ms`'dir
            # ve bu zaten adapter içinde config'den okunuyor.
            text = self.adapter.transcribe(
                audio_np,
                self.language,
                logprob_threshold=self.logprob_threshold,
                no_speech_threshold=self.no_speech_threshold,
                vad_filter=True,
                vad_parameters=None # Beklenmeyen argüman hatasını önlemek için None gönderiyoruz.
            )
            # --- DÜZELTME SONU ---

            if text:
                log.debug("Chunk transcription successful", text=text)
                return {"type": "final", "text": text}
        except Exception as e:
            log.error("Error during transcription chunk", error=str(e), exc_info=True)
            return {"type": "error", "message": "Transcription error"}

        return None

    async def transcribe_stream(self, audio_chunk_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        log.info("Starting audio stream transcription", language=self.language or "auto")

        self.last_audio_time = time.time()
        audio_iterator = audio_chunk_generator.__aiter__()

        while True:
            try:
                chunk = await asyncio.wait_for(audio_iterator.__anext__(), timeout=1.0)
                self.buffer.extend(chunk)
                self.last_audio_time = time.time()

                while len(self.buffer) >= self.chunk_size:
                    process_data = self.buffer[:self.chunk_size]
                    self.buffer = self.buffer[self.chunk_size:]

                    result = await self._process_chunk(process_data)
                    if result:
                        yield result

            except asyncio.TimeoutError:
                if time.time() - self.last_audio_time > self.no_speech_timeout_seconds:
                    log.warn(f"{self.no_speech_timeout_seconds} saniyedir ses algılanmadı. Timeout olayı gönderiliyor.")
                    yield {"type": "no_speech_timeout", "message": "No speech detected."}
                    self.last_audio_time = time.time()

            except StopAsyncIteration:
                log.info("Audio stream ended normally.")
                break

            except Exception as e:
                log.error("Unexpected error in stream processing loop", error=str(e), exc_info=True)
                yield {"type": "error", "message": "Internal processing error."}
                break

        if len(self.buffer) > self.min_chunk_size:
            log.debug("Processing final remaining buffer.", buffer_size=len(self.buffer))
            result = await self._process_chunk(bytes(self.buffer))
            if result:
                yield result

        log.info("Stream transcription finished.")