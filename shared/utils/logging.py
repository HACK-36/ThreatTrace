"""Lightweight logging helpers used across Cerberus services.

Provides a consistent interface for obtaining structured loggers.
"""
from __future__ import annotations

import logging
from typing import Optional


_DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)s | %(name)s | "
    "%(message)s"
)


def configure_root_logger(level: int = logging.INFO, fmt: str = _DEFAULT_FORMAT) -> None:
    """Configure the root logger if it has not already been set up."""
    if not logging.getLogger().handlers:
        logging.basicConfig(level=level, format=fmt)
    else:
        logging.getLogger().setLevel(level)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a module-level logger with default formatting.

    Ensures the root logger is configured before creating child loggers.
    """
    configure_root_logger()
    return logging.getLogger(name)
