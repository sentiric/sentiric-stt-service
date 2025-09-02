import asyncio
from fastapi import FastAPI, Request
from app.core.config import settings
import structlog
from .adapters.base import BaseSTTAdapter
from typing import Dict, Type, Optional

log = structlog.get_logger(__name__)

_ADAPTERS: Dict[str, Type[BaseSTTAdapter]] = {}

def register_adapter(name: str, adapter_class: Type[BaseSTTAdapter]):
    _ADAPTERS[name] = adapter_class
    log.debug("STT adapter registered", adapter_name=name)

async def load_and_set_adapter(app: FastAPI):
    adapter_name = settings.STT_SERVICE_ADAPTER
    log.info(
        "Starting background loading of STT adapter. This may take several minutes depending on the model size...",
        adapter_name=adapter_name,
        model_size=settings.STT_SERVICE_MODEL_SIZE
    )
    
    loop = asyncio.get_event_loop()
    
    try:
        def sync_load():
            adapter_class = _ADAPTERS.get(adapter_name)
            if not adapter_class:
                raise ValueError(f"Invalid STT adapter: {adapter_name}")
            return adapter_class()

        adapter_instance = await loop.run_in_executor(None, sync_load)
        
        app.state.stt_adapter = adapter_instance
        app.state.model_ready = True
        log.info(f"SUCCESS: STT adapter '{adapter_name}' is now loaded and ready.", model_ready=app.state.model_ready)
    except Exception as e:
        app.state.model_ready = False
        app.state.stt_adapter = None
        log.error(f"FATAL: Failed to load adapter '{adapter_name}'", error=str(e), exc_info=True)

def get_adapter(request: Request) -> Optional[BaseSTTAdapter]:
    if not getattr(request.app.state, 'model_ready', False) or not hasattr(request.app.state, 'stt_adapter'):
        return None
    return request.app.state.stt_adapter

from .adapters.faster_whisper_adapter import FasterWhisperAdapter
register_adapter("faster_whisper", FasterWhisperAdapter)

from .adapters.google_live_adapter import GoogleLiveAdapter # YENİ SATIR
register_adapter("google_live", GoogleLiveAdapter) # YENİ SATIR