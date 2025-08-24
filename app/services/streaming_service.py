import numpy as np
import structlog
import webrtcvad
from typing import AsyncGenerator, Optional
from .adapters.base import BaseSTTAdapter

log = structlog.get_logger(__name__)

class AudioProcessor:
    def __init__(self, 
                 adapter: BaseSTTAdapter, 
                 language: str | None = None, 
                 vad_aggressiveness: Optional[int] = None, # Artık opsiyonel
                 logprob_threshold: Optional[float] = None,
                 no_speech_threshold: Optional[float] = None):
        self.adapter = adapter
        self.language = language if language else None
        
        # Eğer dışarıdan geçerli bir VAD seviyesi gelmezse (None veya 0,1,2,3 dışında bir şey),
        # varsayılan olarak en hoşgörülü olan 1'i kullan. Bu, SIP çağrıları için en güvenli ayardır.
        effective_vad_level = vad_aggressiveness if vad_aggressiveness in [0, 1, 2, 3] else 1
        self.vad = webrtcvad.Vad(effective_vad_level)
        log.info("AudioProcessor VAD level set", level=effective_vad_level, source="URL" if vad_aggressiveness is not None else "Default")

        self.logprob_threshold = logprob_threshold
        self.no_speech_threshold = no_speech_threshold
        self.buffer = bytearray()
        self.vad_frame_size = 960  # 30ms @ 16kHz
        self.speech_frames = bytearray()
        self.is_speaking = False
        self.silent_chunks = 0
        self.min_speech_frames = 5 

    async def _process_final_chunk(self):
        if len(self.speech_frames) < self.vad_frame_size * self.min_speech_frames:
            self.speech_frames.clear()
            log.info("Speech frames too short to process, sending empty final transcript.")
            return {"type": "final", "text": ""}
        
        try:
            audio_data = bytes(self.speech_frames)
            self.speech_frames.clear()
            
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0
            
            final_text = self.adapter.transcribe(
                audio_np, 
                self.language,
                logprob_threshold=self.logprob_threshold,
                no_speech_threshold=self.no_speech_threshold
            )

            log.info("Final transcription segment processed", text_length=len(final_text))
            return {"type": "final", "text": final_text}
                
        except Exception as e:
            log.error("Error during final transcription chunk processing", error=str(e), exc_info=True)
            return {"type": "error", "message": "Transcription processing error."}

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
                    # Sessizlik süresini biraz artıralım ki kısa duraksamalarda cümle bölünmesin
                    if self.silent_chunks > 35: # Yaklaşık 1 saniye sessizlik
                        final_result = await self._process_final_chunk()
                        if final_result:
                            yield final_result
                        self.is_speaking = False
                        self.silent_chunks = 0

        # Akış bittiğinde tamponda kalan son konuşmayı da işle
        if self.is_speaking or len(self.speech_frames) > 0:
            final_result = await self._process_final_chunk()
            if final_result:
                yield final_result