# sentiric-stt-service/app/main.py
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

SERVICE_NAME = "stt-service"

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    # DEĞİŞİKLİK: setup_logging'i config'den gelen değerlerle çağır.
    setup_logging(log_level=settings.LOG_LEVEL, env=settings.ENV)
    log = structlog.get_logger().bind(service=SERVICE_NAME)
    
    log.info(
        "Uygulama başlatılıyor...",
        project=settings.PROJECT_NAME,
        version=settings.SERVICE_VERSION,
        commit=settings.GIT_COMMIT,
        build_date=settings.BUILD_DATE,
    )
    
    app.state.model_ready = False
    app.state.stt_adapter = None
    
    loop = asyncio.get_event_loop()
    loop.create_task(stt_service.load_and_set_adapter(app))
    
    yield
    log.info("Uygulama kapatılıyor.")

app = FastAPI(title=settings.PROJECT_NAME, version=settings.SERVICE_VERSION, lifespan=lifespan)
log = structlog.get_logger(__name__)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.middleware("http")
async def logging_middleware(request: Request, call_next) -> Response:
    clear_contextvars()
    
    if request.url.path in ["/health", "/healthz", "/metrics"]:
        return await call_next(request)

    trace_id = request.headers.get("X-Trace-ID") or f"stt-trace-{uuid.uuid4()}"
    bind_contextvars(trace_id=trace_id)
    
    log.info("İstek alındı", http_method=request.method, http_path=request.url.path)
    response = await call_next(request)
    log.info("İstek tamamlandı", http_status_code=response.status_code)
    return response

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health", tags=["Health"])
@app.head("/health")
def health_check(request: Request):
    is_loaded = getattr(request.app.state, 'model_ready', False)
    adapter_type = settings.STT_SERVICE_ADAPTER if is_loaded else "loading"
    status_code = 200 if is_loaded else 503

    response_data = {
        "status": "ok" if is_loaded else "loading_model",
        "adapter_type": adapter_type,
        "model_ready": is_loaded,
        "project": settings.PROJECT_NAME,
        "version": settings.SERVICE_VERSION,
        "commit": settings.GIT_COMMIT,
        "build_date": settings.BUILD_DATE,
    }

    if not is_loaded:
        log.warn("Health check: Model henüz yüklenmedi.", **response_data)
    
    return Response(content=str(response_data), status_code=status_code, media_type="application/json")

@app.get("/healthz", include_in_schema=False)
def healthz_check(request: Request):
    is_loaded = getattr(request.app.state, 'model_ready', False)
    return Response(status_code=200 if is_loaded else 503)

Instrumentator().instrument(app).expose(app)