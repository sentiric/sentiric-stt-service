from contextlib import asynccontextmanager
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.v1.endpoints import router as api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.services.stt_service import load_stt_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Uygulama başlıyor...")
    load_stt_model() # Modeli başlangıçta belleğe yükle
    yield
    logger.info("Uygulama kapanıyor.")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

Instrumentator().instrument(app).expose(app)

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}