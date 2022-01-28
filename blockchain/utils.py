import cchardet
import hashlib
import hmac
import logging
import os
import sys
import uuid
from urllib.parse import urljoin
from typing import TYPE_CHECKING, Any, List, Optional, Union

from fastapi import APIRouter, Request


if TYPE_CHECKING:
    from blockchain.api import schemas
    from blockchain.app import BlockchainWebApp


def get_logger(name: str,
               level: Optional[str] = None,
               force_stdout: bool = False,
               message_format: Optional[str] = None,
               datetime_format: Optional[str] = None,
               file: Optional[str] = None,
               ) -> logging.Logger:
    """
    Immediately sets the logger level to avoid duplicate log outputs from the `root logger` and `this logger` when
    `level` is ``logging.NOTSET``.
    """
    logger = logging.getLogger(name)
    if logger.level == logging.NOTSET:
        # use log level if it was specified via ini config with logger sections, or the package level
        parent_module = os.path.split(os.path.dirname(__file__))[-1]
        level = level or logging.getLogger(parent_module).getEffectiveLevel() or logging.INFO
    if force_stdout or message_format or datetime_format or file:
        set_logger_config(logger, level, force_stdout, message_format, datetime_format, file)
    return logger


def set_logger_config(logger: logging.Logger,
                      level: Optional[int] = None,
                      force_stdout: bool = False,
                      message_format: Optional[str] = None,
                      datetime_format: Optional[str] = None,
                      file: Optional[str] = None,
                      ) -> logging.Logger:
    """
    Applies the provided logging configuration settings to the logger.
    """
    if not logger:
        return logger
    if not level:
        level = logging.INFO
    logger.setLevel(level)
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


def is_uuid(obj: Any) -> bool:
    try:
        uuid.UUID(str(obj))
    except (TypeError, ValueError):
        return False
    return True


def url_strip_slash(path: str) -> str:
    if path.endswith("/") and path != "/":
        return path[:-1]
    return path


def get_links(request: Request, scope: APIRouter, self=True) -> List["schemas.Link"]:
    links = []
    path = url_strip_slash(request.url.path)
    for rule in request.app.routes:
        endpoint = url_strip_slash(rule.path)
        # if the endpoint rule contains a path parameter(s), skip it since it cannot be generated
        if endpoint.startswith(scope.prefix) and "{" not in rule.path:
            rel = endpoint.split("/")[-1] if endpoint != path else "self"
            if rel == "self" and not self:
                continue
            title = rel.replace("_", " ").capitalize()
            href = request.url_for(rule.name)
            links.append({"href": href, "rel": rel, "title": title})
    return links  # type: ignore


def compute_hash(value: Any) -> str:
    from blockchain.app import APP  # import here to avoid circular import and passing secret everywhere

    e_value = str(value).encode("utf-8")
    e_secret = str(APP.secret).encode("utf-8")
    return hmac.new(e_value, msg=e_secret, digestmod=hashlib.sha256).hexdigest()
