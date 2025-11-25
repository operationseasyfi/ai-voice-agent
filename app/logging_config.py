"""
Logging Configuration - Structured logging for production
"""
import logging
import structlog
from app.config import settings


def configure_logging():
    """
    Configure structlog for production logging.
    Uses JSON output in production, console output in development.
    """
    
    # Determine if we're in debug/development mode
    is_development = settings.DEBUG
    
    # Shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    if is_development:
        # Development: Pretty console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Production: JSON output for log aggregation
        processors = shared_processors + [
            structlog.processors.dict_trampoline,
            structlog.processors.JSONRenderer()
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging to integrate with structlog
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO if not is_development else logging.DEBUG,
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str = None):
    """
    Get a structlog logger instance.
    
    Args:
        name: Optional logger name (typically __name__)
        
    Returns:
        Structlog bound logger
    """
    return structlog.get_logger(name)

