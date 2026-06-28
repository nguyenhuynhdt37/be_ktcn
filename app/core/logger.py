import logging
import sys

from loguru import logger

from app.core.config import settings


class InterceptHandler(logging.Handler):
    """
    Custom logging handler to intercept standard library logs
    and route them through Loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        from types import FrameType

        frame: FrameType | None = logging.currentframe()
        depth = 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """
    Initializes and configures the Loguru logger, replacing standard logging handlers.
    """
    # Intercept base logging configuration
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Intercept specific package logs
    loggers_to_intercept = (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "sqlalchemy.engine",
        "alembic",
    )
    for logger_name in loggers_to_intercept:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    # Remove all default handlers from Loguru
    logger.remove()

    # Console Logging
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        enqueue=True,  # Thread-safe logging queue
    )

    # File Logging (with rotation, retention, and compression)
    logger.add(
        settings.LOG_FILE_PATH,
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
    )
