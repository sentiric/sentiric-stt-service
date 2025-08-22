import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from prometheus_fastapi_instrumentator import Instrumentator
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.api.v1.endpoints import router as api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services.stt_service import get_adapter, load_adapter

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Loglamayı burada başlatıyoruz
    setup_logging(log_level=settings.LOG_LEVEL, env=settings.ENV)
    log = structlog.get_logger("lifespan")
    log.info("Application starting up...")
    
    # Modeli başlangıçta yükle
    load_adapter()
    
    yield
    log.info("Application shutting down.")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
log = structlog.get_logger(__name__)

# Middleware: Her istek için loglama ve trace_id
@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> Response:
    clear_contextvars()
    start_time = time.perf_counter()
    
    # Gelen header'dan trace_id'yi al, yoksa yeni bir tane oluştur
    trace_id = request.headers.get("X-Trace-ID") or f"stt-trace-{uuid.uuid4()}"
    bind_contextvars(trace_id=trace_id)

    response = await call_next(request)
    process_time = (time.perf_counter() - start_time) * 1000
    
    log.info(
        "Request completed",
        http_method=request.method,
        http_path=request.url.path,
        http_status_code=response.status_code,
        duration_ms=round(process_time, 2),
    )
    return response

# Prometheus metrikleri için
Instrumentator().instrument(app).expose(app)
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/health", tags=["Health"])
@app.head("/health")
def health_check():
    adapter = get_adapter()
    is_loaded = adapter is not None and getattr(adapter, '_model', None) is not None
    status = {"status": "ok", "adapter_loaded": is_loaded, "adapter_type": settings.STT_SERVICE_ADAPTER}
    log.debug("Health check performed", **status)
    if not is_loaded:
        return Response(content=str(status), status_code=503)
    return status