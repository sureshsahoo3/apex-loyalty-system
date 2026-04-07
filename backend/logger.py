"""Shared logging configuration for Apex Loyalty backend."""
import logging
import sys

_FORMAT = "%(asctime)s  %(levelname)-8s  %(name)-28s  %(message)s"
_DATE   = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """Return a logger that writes formatted text to stdout."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATE))
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False
    return logger
