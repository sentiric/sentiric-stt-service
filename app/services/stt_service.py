# app/services/stt_service.py

from app.core.config import settings
from app.core.logging import logger
from .adapters.base import BaseSTTAdapter

# Adaptörleri burada kaydedeceğiz
_ADAPTERS = {}
_loaded_adapter_instance: BaseSTTAdapter = None

def register_adapter(name: str, adapter_class):
    _ADAPTERS[name] = adapter_class
    logger.debug(f"STT adaptörü kaydedildi: {name}")

def load_adapter() -> BaseSTTAdapter:
    """
    Konfigürasyona göre doğru STT adaptörünü yükler ve bir örneğini döndürür.
    Bu fonksiyon uygulama başlangıcında sadece bir kez çağrılır.
    """
    global _loaded_adapter_instance
    if _loaded_adapter_instance is None:
        adapter_name = settings.STT_ADAPTER
        logger.info(f"Yüklenecek STT adaptörü: {adapter_name}")
        
        adapter_class = _ADAPTERS.get(adapter_name)
        if not adapter_class:
            logger.error(f"Adaptör bulunamadı: {adapter_name}. Kayıtlı adaptörler: {list(_ADAPTERS.keys())}")
            raise ValueError(f"Geçersiz STT adaptörü: {adapter_name}")
            
        _loaded_adapter_instance = adapter_class()
        
    return _loaded_adapter_instance

def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Yüklenmiş olan mevcut adaptörü kullanarak transkripsiyon yapar.
    """
    adapter = load_adapter()
    return adapter.transcribe(audio_bytes)

# --- UYGULAMA BAŞLANGICINDA ADAPTÖRLERİ KAYDET ---
# Bu, "plug-in" sistemimizin temelidir.
from .adapters.faster_whisper_adapter import FasterWhisperAdapter
register_adapter("faster_whisper", FasterWhisperAdapter)

# Gelecekte yeni bir adaptör eklediğimizde, sadece buraya bir satır ekleyeceğiz:
# from .adapters.whisper_cpp_adapter import WhisperCppAdapter
# register_adapter("whisper_cpp", WhisperCppAdapter)