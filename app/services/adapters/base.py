# app/services/adapters/base.py

from abc import ABC, abstractmethod

class BaseSTTAdapter(ABC):
    """
    Tüm STT adaptörleri için temel arayüz (soyut sınıf).
    Her adaptör, bu sınıftan miras almalı ve `transcribe` metodunu uygulamalıdır.
    """
    
    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Verilen ses byte'larını metne çevirir.
        
        Args:
            audio_bytes: İşlenecek ham ses verisi.
            
        Returns:
            Transkripsiyon sonucu olan metin.
        """
        pass