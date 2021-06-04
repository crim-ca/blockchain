import logging
import os
import sys
import uuid
from urllib.parse import urljoin
from typing import TYPE_CHECKING

from flask import request, url_for
from flask import current_app as APP  # noqa

if TYPE_CHECKING:
    from typing import List, Optional, Union

    from flask import Blueprint

    from blockchain import JSON
    from blockchain.api import BlockchainWebApp


def get_logger(name, level=None, force_stdout=None, message_format=None, datetime_format=None, file=None):
    # type: (str, Optional[int], bool, Optional[str], Optional[str], Optional[str]) -> logging.Logger
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
    if force_stdout or message_format or datetime_format or file:
        set_logger_config(logger, force_stdout, message_format, datetime_format, file)
    return logger


def set_logger_config(logger, force_stdout=False, message_format=None, datetime_format=None, file=None):
    # type: (logging.Logger, bool, Optional[str], Optional[str], Optional[str]) -> logging.Logger
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
    if file:
        handler = logging.FileHandler(file)
        if message_format or datetime_format:
            handler.setFormatter(logging.Formatter(fmt=message_format, datefmt=datetime_format))
        logger.addHandler(handler)
    return logger


def is_uuid(obj):
    try:
        uuid.UUID(str(obj))
    except (TypeError, ValueError):
        return False
    return True


def get_links(scope, ):
    # type: (Union[Blueprint, BlockchainWebApp]) -> List[JSON]
    links = []
    scope = scope.name + "."
    for rule in APP.url_map.iter_rules():
        endpoint = rule.endpoint
        if endpoint.startswith(scope) and "<" not in str(rule) and ">" not in str(rule):
            rel = endpoint.split(".")[-1] if endpoint != request.endpoint else "self"
            links.append({"href": urljoin(request.url, url_for(endpoint)), "rel": rel})
    return links
