# sentiric-stt-service/app/services/streaming_service.py
import time
import collections
import webrtcvad
import numpy as np
import structlog
from typing import AsyncGenerator, Optional
from .adapters.base import BaseSTTAdapter
from app.core.config import settings

log = structlog.get_logger(__name__)

class AudioProcessor:
    def __init__(self,
                 adapter: BaseSTTAdapter,
                 language: str | None = None,
                 logprob_threshold: Optional[float] = None,
                 no_speech_threshold: Optional[float] = None):
        
        self.adapter = adapter
        self.language = language
        self.logprob_threshold = logprob_threshold
        self.no_speech_threshold = no_speech_threshold

        # VAD'ı yapılandır
        self.vad = webrtcvad.Vad()
        try:
            # Ortam değişkeninden gelen değeri kullan
            aggressiveness = settings.STT_SERVICE_VAD_AGGRESSIVENESS
            self.vad.set_mode(aggressiveness)
            log.info("VAD initialized", aggressiveness=aggressiveness)
        except Exception as e:
            log.error("Failed to set VAD mode, defaulting to 1.", error=str(e))
            self.vad.set_mode(1) # Hata durumunda güvenli bir varsayılana dön

        # VAD, 10, 20 veya 30 ms'lik frame'ler üzerinde çalışır. 30ms en verimlisidir.
        self.frame_duration_ms = 30
        # 16-bit PCM (2 byte) * 16000 sample/s -> 32000 byte/s
        # 30ms'lik bir frame'in byte cinsinden boyutu
        self.frame_size_bytes = int(16000 * 2 * (self.frame_duration_ms / 1000.0))

        # Konuşma tespiti için kullanılan parametreler
        self.padding_duration_ms = settings.STT_SERVICE_VAD_PADDING_MS
        self.min_speech_duration_ms = settings.STT_SERVICE_VAD_MIN_SPEECH_MS
        self.end_of_speech_silence_ms = settings.STT_SERVICE_VAD_END_OF_SPEECH_MS
        
        # Ring buffer, belirli bir süre boyunca ses frame'lerini tutar
        self.ring_buffer_frames = int(self.padding_duration_ms / self.frame_duration_ms)
        self.ring_buffer = collections.deque(maxlen=self.ring_buffer_frames)

        # Durum değişkenleri
        self.triggered = False
        self.speech_frames = []
        self.silence_frames_count = 0
        self.last_activity = time.time()
        self.no_speech_timeout_seconds = 10 # Uzun sessizlikler için timeout

    async def _process_utterance(self) -> dict | None:
        """Birikmiş konuşma sesini (utterance) işler ve transkripsiyon yapar."""
        if not self.speech_frames:
            return None

        # Konuşmanın toplam süresini hesapla
        speech_duration_ms = len(self.speech_frames) * self.frame_duration_ms
        if speech_duration_ms < self.min_speech_duration_ms:
            log.warn("Skipping transcription for very short speech.", duration_ms=speech_duration_ms)
            self.speech_frames.clear()
            return None

        log.info(f"Processing a speech segment of {speech_duration_ms / 1000:.2f} seconds.")
        
        # Tüm ses frame'lerini tek bir byte dizisine birleştir
        audio_data = b''.join(self.speech_frames)
        self.speech_frames.clear()

        try:
            # Byte dizisini modele uygun float array'e çevir
            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32767.0
            
            text = self.adapter.transcribe(
                audio_np,
                self.language,
                logprob_threshold=self.logprob_threshold,
                no_speech_threshold=self.no_speech_threshold
            )

            if text:
                log.info("Transcription successful", text=text)
                return {"type": "final", "text": text}
            else:
                log.warn("Transcription resulted in empty text, likely due to noise or non-speech.")
                return None
                
        except Exception as e:
            log.error("Error during transcription of utterance", error=str(e), exc_info=True)
            return {"type": "error", "message": "Transcription error"}

    async def transcribe_stream(self, audio_chunk_generator: AsyncGenerator[bytes, None]) -> AsyncGenerator[dict, None]:
        log.info("Starting VAD-based audio stream transcription", language=self.language or "auto")

        buffer = bytearray()
        end_of_speech_frames_needed = self.end_of_speech_silence_ms // self.frame_duration_ms

        async for chunk in audio_chunk_generator:
            buffer.extend(chunk)
            self.last_activity = time.time()

            while len(buffer) >= self.frame_size_bytes:
                frame = buffer[:self.frame_size_bytes]
                buffer = buffer[self.frame_size_bytes:]
                
                is_speech = self.vad.is_speech(frame, 16000)

                if not self.triggered:
                    # Konuşma başlamadıysa, frame'i ring buffer'a ekle
                    self.ring_buffer.append((frame, is_speech))
                    num_voiced = len([f for f, speech in self.ring_buffer if speech])
                    
                    # Ring buffer'daki frame'lerin çoğu konuşma ise, konuşma başladı (triggered)
                    if num_voiced > 0.9 * self.ring_buffer.maxlen:
                        self.triggered = True
                        log.info("VAD: Speech detected, started capturing utterance.")
                        # Konuşmanın başındaki sessiz kısımları da al
                        for f, s in self.ring_buffer:
                            self.speech_frames.append(f)
                        self.ring_buffer.clear()
                else:
                    # Konuşma devam ediyorsa, frame'i doğrudan biriktir
                    self.speech_frames.append(frame)
                    # Sessizlik anlarını say
                    if not is_speech:
                        self.silence_frames_count += 1
                    else:
                        self.silence_frames_count = 0 # Konuşma varsa sayacı sıfırla

                    # Belirlenen süre kadar sessizlik olduysa, cümlenin bittiğini varsay
                    if self.silence_frames_count > end_of_speech_frames_needed:
                        log.info("VAD: End of speech detected due to silence.")
                        result = await self._process_utterance()
                        if result:
                            yield result
                        
                        # Durumu sıfırla ve yeni bir cümle için hazır ol
                        self.triggered = False
                        self.silence_frames_count = 0

        # Döngü bittiğinde, buffer'da kalan son konuşma parçasını işle
        log.info("Audio stream ended. Processing any final buffered speech.")
        if self.speech_frames:
            result = await self._process_utterance()
            if result:
                yield result
        
        log.info("VAD-based stream transcription finished.")