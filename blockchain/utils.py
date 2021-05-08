import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


def get_logger(name, level=None, force_stdout=None, message_format=None, datetime_format=None):
    # type: (str, Optional[int], bool, Optional[str], Optional[str]) -> logging.Logger
    """
    Immediately sets the logger level to avoid duplicate log outputs from the `root logger` and `this logger` when
    `level` is ``logging.NOTSET``.
    """
    logger = logging.getLogger(name)
    if logger.level == logging.NOTSET:
        # use log level if it was specified via ini config with logger sections, or the package level
        parent_module = os.path.split(os.path.dirname(__file__))[-1]
        level = level or logging.getLogger(parent_module).getEffectiveLevel() or logging.INFO
        logger.setLevel(level)
    if force_stdout or message_format or datetime_format:
        set_logger_config(logger, force_stdout, message_format, datetime_format)
    return logger


def set_logger_config(logger, force_stdout=False, message_format=None, datetime_format=None):
    # type: (logging.Logger, bool, Optional[str], Optional[str]) -> logging.Logger
    """
    Applies the provided logging configuration settings to the logger.
    """
    if not logger:
        return logger
    handler = None
    if force_stdout:
        all_handlers = logging.root.handlers + logger.handlers
        if not any(isinstance(h, logging.StreamHandler) for h in all_handlers):
            handler = logging.StreamHandler(sys.stdout)
            logger.addHandler(handler)  # noqa: type
    if not handler:
        if logger.handlers:
            handler = logger.handlers
        else:
            handler = logging.StreamHandler(sys.stdout)
            logger.addHandler(handler)
    if message_format or datetime_format:
        handler.setFormatter(logging.Formatter(fmt=message_format, datefmt=datetime_format))
    return logger
