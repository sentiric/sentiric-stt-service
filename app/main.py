from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.endpoints import router as api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging, logger

# DÜZELTME: Doğru fonksiyonu import ediyoruz
from app.services.stt_service import load_adapter

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(log_level=settings.LOG_LEVEL, env=settings.ENV)
    
    logger.info("Uygulama başlıyor...")
    # DÜZELTME: Doğru fonksiyonu çağırıyoruz
    load_adapter() # Konfigürasyondaki adaptörü başlangıçta yükle
    yield
    logger.info("Uygulama kapanıyor.")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

Instrumentator().instrument(app).expose(app)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
@app.head("/health")
def health_check():
    try:
        # DÜZELTME: Doğru fonksiyonu çağırıyoruz
        adapter = load_adapter()
        if adapter:
            return {
                "status": "ok", 
                "adapter_loaded": True, 
                "adapter_type": settings.STT_ADAPTER
            }
        else:
            return {"status": "error", "adapter_loaded": False, "detail": "Adapter is not loaded."}
    except Exception as e:
         return {"status": "error", "adapter_loaded": False, "detail": str(e)}