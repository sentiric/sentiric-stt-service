import logging
import sys
import structlog
from structlog.contextvars import merge_contextvars

# Bu, structlog'un log seviyesini standart logging ile senkronize etmesini sağlar.
structlog.configure(
    processors=[
        merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def setup_logging(log_level: str, env: str):
    log_level = log_level.upper()
    
    # Formatter'ı structlog'un kendi işlemcileriyle oluşturuyoruz
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
        ],
        processor=structlog.dev.ConsoleRenderer() if env == "development" else structlog.processors.JSONRenderer(),
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
    # Uvicorn loglarını da yakalamak için
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.error").handlers = [handler]

    logger = structlog.get_logger("sentiric-stt-service")
    logger.info("Logging configured", log_level=log_level, environment=env)
    return logger

logger = structlog.get_logger()