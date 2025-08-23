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
    start_time = time.perf_counter()
    
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

app.include_router(api_v1_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health", tags=["Health"])
@app.head("/health")
def health_check(request: Request):
    is_loaded = getattr(request.app.state, 'model_ready', False)

    if not is_loaded:
        status = {"status": "loading_model", "model_ready": is_loaded, "adapter_type": settings.STT_SERVICE_ADAPTER}
        log.warn("Health check failed: Model is not loaded yet.", **status)
        return Response(content=str(status), status_code=503, media_type="application/json")
    
    status = {"status": "ok", "model_ready": is_loaded, "adapter_type": settings.STT_SERVICE_ADAPTER}
    log.debug("Health check performed successfully", **status)
    return status

Instrumentator().instrument(app).expose(app)