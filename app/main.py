# sentiric-stt-service/app/main.py

import time
import uuid
import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_fastapi_instrumentator import Instrumentator
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.api.v1.endpoints import router as api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.services import stt_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(log_level=settings.LOG_LEVEL, env=settings.ENV)
    log = structlog.get_logger("lifespan")
    log.info("Application starting up...")
    
    app.state.model_ready = False
    app.state.stt_adapter = None
    
    loop = asyncio.get_event_loop()
    loop.create_task(stt_service.load_and_set_adapter(app))
    
    yield
    log.info("Application shutting down.")

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
log = structlog.get_logger(__name__)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> Response:
    clear_contextvars()
    
    if request.url.path == "/healthz":
        return await call_next(request)

    trace_id = request.headers.get("X-Trace-ID") or f"stt-trace-{uuid.uuid4()}"
    bind_contextvars(trace_id=trace_id)
    
    log.info(
        "Request received",
        http_method=request.method,
        http_path=request.url.path
    )

    response = await call_next(request)

    log.info(
        "Request completed",
        http_method=request.method,
        http_path=request.url.path,
        http_status_code=response.status_code,
    )
    return response

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health", tags=["Health"])
@app.head("/health")
def health_check(request: Request):
    # app.state üzerinden modelin hazır olup olmadığını kontrol et
    is_loaded = getattr(request.app.state, 'model_ready', False)

    if not is_loaded:
        status = {"status": "loading_model", "model_ready": is_loaded, "adapter_type": settings.STT_SERVICE_ADAPTER}
        log.warn("Health check failed: Model is not loaded yet.", **status)
        # Model hazır değilse 503 Service Unavailable döndür.
        # Docker'ın healthcheck'i bu sayede servisin "unhealthy" olduğunu anlayacak.
        return Response(content=str(status), status_code=503, media_type="application/json")
    
    status = {"status": "ok", "model_ready": is_loaded, "adapter_type": settings.STT_SERVICE_ADAPTER}
    log.debug("Health check performed successfully", **status)
    return status

@app.get("/healthz", include_in_schema=False)
def healthz_check(request: Request): # request parametresini ekleyelim
    # app.state üzerinden modelin hazır olup olmadığını kontrol et
    is_loaded = getattr(request.app.state, 'model_ready', False)
    if not is_loaded:
        # Model yüklenirken bile bu endpoint'in 200 dönmesi,
        # container'ın en azından çalıştığını gösterir.
        return Response(status_code=503)
    return Response(status_code=200)

Instrumentator().instrument(app).expose(app)