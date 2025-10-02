# sentiric-stt-service/app/core/logging.py
import logging
import sys
import structlog

def setup_logging(log_level: str, env: str):
    """
    Uygulama genelinde yapısal loglamayı (structlog) ayarlar.
    Gürültücü kütüphanelerin log seviyelerini yükselterek ana uygulama
    loglarının okunabilirliğini artırır.
    """
    log_level = log_level.upper()

    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Geliştirme ortamında daha okunaklı, renkli loglar kullan
    if env == "development":
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    # Üretim ortamında JSON formatında log bas
    else:
        processors = shared_processors + [structlog.processors.JSONRenderer()]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # structlog'u standart logging ile entegre et
    handler = logging.StreamHandler(sys.stdout)
    
    root_logger = logging.getLogger()
    # Mevcut handler'ları temizleyip sadece bizimkini ekliyoruz
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    # Gürültücü kütüphanelerin log seviyesini WARNING'e çekerek
    # DEBUG ve INFO seviyesindeki spam'lerini engelle
    noisy_libraries = [
        "faster_whisper", 
        "huggingface_hub", 
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access", 
        "websockets"
    ]
    for lib_name in noisy_libraries:
        logging.getLogger(lib_name).setLevel(logging.WARNING)
    
    # Sadece kendi uygulama loglarımızın belirlenen seviyede akmasını sağla
    # Bu, root logger'ın seviyesini korurken kütüphaneleri susturur.
    log = structlog.get_logger()
    log.info("Logging configured", log_level=log_level, env=env)