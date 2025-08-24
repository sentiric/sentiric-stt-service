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
        # Her 1.5 saniyede bir transkripsiyon yapmaya zorla (veya o kadar ses biriktiğinde)
        self.bytes_per_ms = 32  # 16kHz, 16-bit PCM = 32000 bytes/s = 32 bytes/ms
        self.chunk_size = int(1.5 * 1000 * self.bytes_per_ms) 
        self.min_chunk_size = int(0.5 * 1000 * self.bytes_per_ms) # En az 0.5 saniyelik ses

    async def _process_chunk(self, audio_chunk: bytes):
        """Yardımcı fonksiyon: Gelen ses parçasını işler ve sonucu döndürür."""
        try:
            audio_np = np.frombuffer(audio_chunk, dtype=np.int16).astype(np.float32) / 32767.0
            
            text = self.adapter.transcribe(
                audio_np, 
                self.language,
                logprob_threshold=self.logprob_threshold,
                no_speech_threshold=self.no_speech_threshold,
                vad_filter=True  # Whisper'ın kendi VAD'ını kullanmasını sağlıyoruz
            )

            if text:
                log.info("Forced transcription successful", text=text)
                return {"type": "final", "text": text}
        except Exception as e:
            log.error("Error during forced transcription chunk", error=str(e), exc_info=True)
            return {"type": "error", "message": "Transcription error"}
        
        return None

    async def transcribe_stream(self, audio_chunk_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        log.info(
            "Starting audio stream transcription in FORCED mode", 
            language=self.language or "auto",
            chunk_size_bytes=self.chunk_size
        )
        
        async for chunk in audio_chunk_generator:
            self.buffer.extend(chunk)

            # Yeterli veri biriktiğinde, beklemeden işlemi yap
            while len(self.buffer) >= self.chunk_size:
                process_data = self.buffer[:self.chunk_size]
                self.buffer = self.buffer[self.chunk_size:]
                
                result = await self._process_chunk(process_data)
                if result:
                    yield result
        
        # Akış bittiğinde arta kalanları da işle (eğer yeterince büyükse)
        if len(self.buffer) > self.min_chunk_size:
            result = await self._process_chunk(bytes(self.buffer))
            if result:
                yield result