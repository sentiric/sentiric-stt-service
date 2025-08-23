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
        # Yabancı (uvicorn gibi) loglar için de temel işlemcileri ekle
        foreign_pre_chain=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
        ],
        processor=structlog.dev.ConsoleRenderer() if env == "development" else structlog.processors.JSONRenderer(),
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    # Önceki handler'ları temizleyerek çift loglamayı engelle
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    
    # Uvicorn loglarını da yakalayıp bizim handler'ımızı kullanmaya zorla
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        uvicorn_logger = logging.getLogger(logger_name)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False # Mesajın root logger'a tekrar gitmesini engelle

    logger = structlog.get_logger("sentiric-stt-service")
    logger.info("Logging configured", log_level=log_level, environment=env)
    return logger

logger = structlog.get_logger()