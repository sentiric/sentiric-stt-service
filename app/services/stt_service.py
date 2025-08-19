from app.core.config import settings
from app.core.logging import logger
from .adapters.base import BaseSTTAdapter
from typing import Optional # YENİ

_ADAPTERS = {}
_loaded_adapter_instance: BaseSTTAdapter = None

def register_adapter(name: str, adapter_class):
    _ADAPTERS[name] = adapter_class
    logger.debug(f"STT adaptörü kaydedildi: {name}")

def load_adapter() -> BaseSTTAdapter:
    global _loaded_adapter_instance
    if _loaded_adapter_instance is None:
        adapter_name = settings.STT_SERVICE_ADAPTER
        logger.info(f"Yüklenecek STT adaptörü: {adapter_name}")
        adapter_class = _ADAPTERS.get(adapter_name)
        if not adapter_class:
            logger.error(f"Adaptör bulunamadı: {adapter_name}. Kayıtlı adaptörler: {list(_ADAPTERS.keys())}")
            raise ValueError(f"Geçersiz STT adaptörü: {adapter_name}")
        _loaded_adapter_instance = adapter_class()
    return _loaded_adapter_instance

# DÜZELTME: Fonksiyon artık opsiyonel bir 'language' parametresi alıyor.
def transcribe_audio(audio_bytes: bytes, language: Optional[str] = None) -> str:
    adapter = load_adapter()
    return adapter.transcribe(audio_bytes, language)

from .adapters.faster_whisper_adapter import FasterWhisperAdapter
register_adapter("faster_whisper", FasterWhisperAdapter)