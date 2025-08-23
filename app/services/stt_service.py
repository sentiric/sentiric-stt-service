import asyncio
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

async def load_adapter():
    """Modeli ve adaptörü asenkron olarak yükler."""
    global _loaded_adapter_instance
    if _loaded_adapter_instance is None:
        adapter_name = settings.STT_SERVICE_ADAPTER
        log.info(f"Starting background loading of STT adapter: {adapter_name}")
        
        loop = asyncio.get_event_loop()
        
        try:
            def sync_load():
                adapter_class = _ADAPTERS.get(adapter_name)
                if not adapter_class:
                    raise ValueError(f"Invalid STT adapter: {adapter_name}")
                # Bu çağrı artık __init__ içinde modeli yükleyecek
                return adapter_class()

            _loaded_adapter_instance = await loop.run_in_executor(None, sync_load)
            log.info(f"STT adapter '{adapter_name}' loaded and ready in background.")
        except Exception as e:
            log.error(f"FATAL: Failed to load adapter '{adapter_name}' in background", error=str(e), exc_info=True)
            _loaded_adapter_instance = None # Başarısızlık durumunda None olarak ayarla

def get_adapter() -> Optional[BaseSTTAdapter]:
    return _loaded_adapter_instance

def transcribe_audio(audio_bytes: bytes, language: Optional[str] = None) -> str:
    adapter = get_adapter()
    if not adapter or not getattr(adapter, 'model_loaded', False):
        log.error("Transcription failed because STT adapter is not loaded or ready.")
        raise RuntimeError("STT adapter is not loaded. Cannot transcribe audio.")
    return adapter.transcribe(audio_bytes, language)

# Adaptörleri burada kaydediyoruz
from .adapters.faster_whisper_adapter import FasterWhisperAdapter
register_adapter("faster_whisper", FasterWhisperAdapter)