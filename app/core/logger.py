from __future__ import annotations

import logging
import sys


def build_logger(name: str, debug: bool) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG if debug else logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger


def should_log_partial_results(
    logger: logging.Logger,
    force_enabled: bool = False,
) -> bool:
    return force_enabled or logger.isEnabledFor(logging.DEBUG)


def log_partial_result(
    logger: logging.Logger,
    force_enabled: bool,
    message: str,
    *args: object,
) -> None:
    if should_log_partial_results(logger, force_enabled):
        logger.debug("[partial] " + message, *args)
