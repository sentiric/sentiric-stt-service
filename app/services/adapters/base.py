from abc import ABC, abstractmethod
from typing import Optional

class BaseSTTAdapter(ABC):
    """
    Tüm STT adaptörleri için temel arayüz.
    """
    
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, language: Optional[str] = None) -> str:
        """
        Verilen ses byte'larını metne çevirir.
        
        Args:
            audio_bytes: İşlenecek ham ses verisi.
            language: Metne çevrilecek dilin kodu (örn: "tr", "en").
                      Eğer None ise, model otomatik dil tespiti yapar.
            
        Returns:
            Transkripsiyon sonucu olan metin.
        """
        pass