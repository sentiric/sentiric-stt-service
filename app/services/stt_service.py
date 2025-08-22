from app.core.config import settings
import structlog
from .adapters.base import BaseSTTAdapter
from typing import Optional, Dict, Type

log = structlog.get_logger(__name__)

_ADAPTERS: Dict[str, Type[BaseSTTAdapter]] = {}
_loaded_adapter_instance: Optional[BaseSTTAdapter] = None

def register_adapter(name: str, adapter_class: Type[BaseSTTAdapter]):
    _ADAPTERS[name] = adapter_class
    log.debug("STT adapter registered", adapter_name=name)

def load_adapter():
    global _loaded_adapter_instance
    if _loaded_adapter_instance is None:
        adapter_name = settings.STT_SERVICE_ADAPTER
        log.info(f"Loading STT adapter: {adapter_name}")
        adapter_class = _ADAPTERS.get(adapter_name)
        if not adapter_class:
            log.error(f"Adapter not found: {adapter_name}. Registered adapters: {list(_ADAPTERS.keys())}")
            raise ValueError(f"Invalid STT adapter: {adapter_name}")
        _loaded_adapter_instance = adapter_class()

def get_adapter() -> Optional[BaseSTTAdapter]:
    return _loaded_adapter_instance

def transcribe_audio(audio_bytes: bytes, language: Optional[str] = None) -> str:
    adapter = get_adapter()
    if not adapter:
        raise RuntimeError("STT adapter is not loaded. Cannot transcribe audio.")
    return adapter.transcribe(audio_bytes, language)

# Adaptörleri burada kaydediyoruz
from .adapters.faster_whisper_adapter import FasterWhisperAdapter
register_adapter("faster_whisper", FasterWhisperAdapter)