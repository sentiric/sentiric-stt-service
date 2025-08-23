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
        
        self.language = language
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.buffer = bytearray()
        # VAD 10, 20, 30 ms'lik frame'ler bekler. 30ms = 16000 Hz * 2 bytes/sample * 0.030s = 960 bytes
        self.vad_frame_size = 960

    async def transcribe_stream(self, audio_chunk_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        """
        Gelen ses akışını işler, VAD uygular ve transkripsiyon sonuçlarını anlık olarak döndürür.
        """
        log.info("Starting audio stream transcription", language=self.language or "auto")
        
        async for chunk in audio_chunk_generator:
            self.buffer.extend(chunk)

            while len(self.buffer) >= self.vad_frame_size:
                frame = self.buffer[:self.vad_frame_size]
                self.buffer = self.buffer[self.vad_frame_size:]

                # VAD ile ses aktivitesi tespiti yap (bu kısmı daha da geliştirebiliriz)
                # Şimdilik, belirli bir miktar veri biriktiğinde transkripsiyonu tetikleyelim
                # Örnek: her 1 saniyelik ses biriktiğinde (16000 * 2 bytes)
                if len(self.buffer) > 16000 * 2:
                    audio_to_transcribe = bytes(self.buffer)
                    self.buffer.clear() # Buffer'ı temizle
                    
                    try:
                        # Numpy array'e çevir
                        audio_np = np.frombuffer(audio_to_transcribe, dtype=np.int16).astype(np.float32) / 32768.0
                        
                        segments, info = self.adapter._model.transcribe(audio_np, language=self.language)
                        
                        # Geçici (interim) ve final sonuçları gönder
                        full_text = "".join(s.text for s in segments)
                        
                        log.debug("Partial transcription generated", text_length=len(full_text))
                        yield {"type": "partial", "text": full_text}

                    except Exception as e:
                        log.error("Error during partial transcription", error=str(e))
                        yield {"type": "error", "message": str(e)}

        # Akış bittiğinde buffer'da kalan son veriyi de işle
        if self.buffer:
            try:
                audio_np = np.frombuffer(bytes(self.buffer), dtype=np.int16).astype(np.float32) / 32768.0
                segments, info = self.adapter._model.transcribe(audio_np, language=self.language)
                final_text = "".join(s.text for s in segments).strip()
                
                log.info("Final transcription generated", text_length=len(final_text), detected_language=info.language)
                yield {"type": "final", "text": final_text, "language": info.language}
            except Exception as e:
                log.error("Error during final transcription", error=str(e))
                yield {"type": "error", "message": str(e)}