# app/services/streaming_service.py dosyasının TAM ve GÜNCELLENMİŞ HALİ
import time # --- YENİ ---
import numpy as np
import structlog
from typing import AsyncGenerator, Optional
from .adapters.base import BaseSTTAdapter

log = structlog.get_logger(__name__)

class AudioProcessor:
    def __init__(self, 
                 adapter: BaseSTTAdapter, 
                 language: str | None = None, 
                 vad_aggressiveness: Optional[int] = None,
                 logprob_threshold: Optional[float] = None,
                 no_speech_threshold: Optional[float] = None):
        self.adapter = adapter
        self.language = language
        self.logprob_threshold = logprob_threshold
        self.no_speech_threshold = no_speech_threshold
        
        self.buffer = bytearray()
        self.bytes_per_ms = 32
        self.chunk_size = int(1.5 * 1000 * self.bytes_per_ms) 
        self.min_chunk_size = int(0.5 * 1000 * self.bytes_per_ms)
        
        # --- YENİ: Timeout yönetimi için değişkenler ---
        self.last_audio_time = time.time()
        self.no_speech_timeout_seconds = 10  # 10 saniye sessizlikten sonra timeout

    async def _process_chunk(self, audio_chunk: bytes):
        try:
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32767.0
            
            text = self.adapter.transcribe(
                audio_np, 
                self.language,
                logprob_threshold=self.logprob_threshold,
                no_speech_threshold=self.no_speech_threshold,
                vad_filter=True
            )

            if text:
                log.info("Forced transcription successful", text=text)
                return {"type": "final", "text": text}
        except Exception as e:
            log.error("Error during forced transcription chunk", error=str(e), exc_info=True)
            return {"type": "error", "message": "Transcription error"}
        
        return None

    async def transcribe_stream(self, audio_chunk_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        log.info("Starting audio stream transcription", language=self.language or "auto")
        
        self.last_audio_time = time.time() # Başlangıç zamanını ayarla

        async for chunk in audio_chunk_generator:
            self.buffer.extend(chunk)
            self.last_audio_time = time.time() # Her ses paketi geldiğinde zamanı güncelle

            while len(self.buffer) >= self.chunk_size:
                process_data = self.buffer[:self.chunk_size]
                self.buffer = self.buffer[self.chunk_size:]
                
                result = await self._process_chunk(process_data)
                if result:
                    yield result
            
            # --- YENİ: Timeout kontrolü ---
            # Bu blok, audio_chunk_generator'dan veri gelmediğinde çalışır
            if time.time() - self.last_audio_time > self.no_speech_timeout_seconds:
                log.warning(f"No speech detected for {self.no_speech_timeout_seconds} seconds. Sending timeout event.")
                yield {"type": "no_speech_timeout", "message": "No speech detected."}
                self.last_audio_time = time.time() # Timeout sonrası tekrar sayacı sıfırla

        if len(self.buffer) > self.min_chunk_size:
            result = await self._process_chunk(bytes(self.buffer))
            if result:
                yield result