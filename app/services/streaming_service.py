import numpy as np
import structlog
# import webrtcvad # <-- Bu satırı SİLİN veya yorum satırı yapın
from typing import AsyncGenerator, Optional
from .adapters.base import BaseSTTAdapter

log = structlog.get_logger(__name__)

class AudioProcessor:
    def __init__(self, 
                 adapter: BaseSTTAdapter, 
                 language: str | None = None, 
                 vad_aggressiveness: Optional[int] = None, # Bu parametre artık kullanılmayacak ama uyumluluk için kalabilir
                 logprob_threshold: Optional[float] = None,
                 no_speech_threshold: Optional[float] = None):
        self.adapter = adapter
        self.language = language if language else None
        # self.vad = webrtcvad.Vad(...) # <-- Bu satırı SİLİN
        self.logprob_threshold = logprob_threshold
        self.no_speech_threshold = no_speech_threshold
        
        self.buffer = bytearray()
        # Sesi biriktirmek için bir zaman sınırı belirleyelim (örn: 5 saniye)
        self.max_chunk_duration_ms = 5000
        self.bytes_per_ms = 32 # 16kHz, 16-bit PCM = 32000 bytes/s = 32 bytes/ms
        self.max_buffer_size = self.max_chunk_duration_ms * self.bytes_per_ms
        self.min_buffer_size = 500 * self.bytes_per_ms # En az yarım saniyelik ses biriktir

    async def _process_final_chunk(self):
        if len(self.buffer) < self.min_buffer_size:
            self.buffer.clear()
            log.info("Buffer too short to process, clearing.")
            return {"type": "final", "text": ""}
        
        try:
            audio_data = bytes(self.buffer)
            self.buffer.clear()
            
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0
            
            # Artık transkripsiyonu burada çağırıyoruz
            final_text = self.adapter.transcribe(
                audio_np, 
                self.language,
                logprob_threshold=self.logprob_threshold,
                no_speech_threshold=self.no_speech_threshold,
                # Whisper'a VAD'ı kullanmasını söylüyoruz
                vad_filter=True 
            )

            log.info("Final transcription segment processed", text_length=len(final_text))
            return {"type": "final", "text": final_text}
                
        except Exception as e:
            log.error("Error during final transcription chunk processing", error=str(e), exc_info=True)
            return {"type": "error", "message": "Transcription processing error."}

    async def transcribe_stream(self, audio_chunk_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        log.info("Starting audio stream transcription with internal VAD", language=self.language or "auto")
        
        async for chunk in audio_chunk_generator:
            self.buffer.extend(chunk)

            # Belirli bir boyuta ulaştığında veya akış bittiğinde işlem yap
            if len(self.buffer) >= self.max_buffer_size:
                final_result = await self._process_final_chunk()
                if final_result and final_result["text"]: # Sadece dolu metin gelirse gönder
                    yield final_result
        
        # Akış bittiğinde tamponda kalan son konuşmayı da işle
        if len(self.buffer) > self.min_buffer_size:
            final_result = await self._process_final_chunk()
            if final_result:
                yield final_result