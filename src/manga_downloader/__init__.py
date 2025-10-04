"""Manga Downloader - A CLI tool to download manga and convert to PDF."""

import sys

from loguru import logger

__version__ = "0.1.0"

# Configure loguru logger
logger.remove()  # Remove default handler

# Add console handler with custom format
logger.add(
    sys.stdout,
    format="<level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Add file handler for persistent logging
logger.add(
    "manga_downloader.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
)


def set_log_level(verbose: bool = False) -> None:
    """Set the logging level based on verbosity."""
    level = "DEBUG" if verbose else "INFO"
    logger.remove()
    logger.add(
        sys.stdout,
        format="<level>{message}</level>",
        level=level,
        colorize=True,
    )
    logger.add(
        "manga_downloader.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
    )
