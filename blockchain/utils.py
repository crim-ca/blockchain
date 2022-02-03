import copy
import hashlib
import hmac
import json
import logging
import os
import sys
import uuid
from urllib.parse import urljoin
from typing import TYPE_CHECKING, Any, Coroutine, List, Optional, Union

from fastapi import APIRouter, HTTPException, Request
from requests_toolbelt import multipart
from uvicorn.config import LOGGING_CONFIG

from blockchain.typedefs import JSON

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


def update_uvicorn_logger_config(logger: logging.Logger) -> dict:
    config = copy.deepcopy(LOGGING_CONFIG)
    if logger and logger.handlers:
        handler = logger.handlers[0]
        if handler.formatter:
            fmt = handler.formatter
            msg = fmt._fmt  # noqa
            for log_fmt in config.get("formatters", {}).values():
                msg_fmt = log_fmt["fmt"]
                for field in ["levelprefix", "levelname"]:
                    field_fmt = f"%({field})s"
                    if field_fmt in msg_fmt:
                        msg_fmt = msg_fmt.replace(field_fmt + " ", "")
                        msg_fmt = msg_fmt.replace(field_fmt, "")
                msg_fmt = msg.replace("%(message)s", msg_fmt)
                log_fmt["fmt"] = msg_fmt
    return config


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


async def parse_multipart_consents(request: Request) -> JSON:
    """
    Parse multipart body expecting boundaries defining different consents metadata.

    .. seealso::
        https://github.com/crim-ca/blockchain/blob/master/docs/consents.md#encoded-data-consents

    :param request: Request with multipart body.
    :return: Mapping of parsed body parts with corresponding ID
    """
    body = request.body()
    if isinstance(body, Coroutine):
        body = await body
    try:
        content_type = request.headers["Content-Type"]
        decoded_body = multipart.decoder.MultipartDecoder(body, content_type)
    except multipart.decoder.ImproperBodyPartContentException as exc:
        raise HTTPException(422, f"Multipart body or sub-part failed parsing. Detail: [{exc!s}]")
    except multipart.decoder.NonMultipartContentTypeException as exc:
        raise HTTPException(422, f"Multipart body could not be parsed. Detail: [{exc!s}]")
    except TypeError as exc:
        raise HTTPException(400, f"Multipart body has invalid Content-Type. Detail: [{exc!s}]")
    if len(decoded_body.parts) < 1:
        raise HTTPException(400, f"Multipart body failed to retrieve any valid content part.")
    # search for JSON meta part
    meta = None
    meta_index = -1
    for i, part in enumerate(decoded_body.parts):
        c_type = part.headers.get(b"Content-Type", b"")
        c_id = part.headers.get(b"Content-ID")
        if c_type.startswith(b"application/json") and c_id == b"meta":
            try:
                meta = json.loads(part.text)
            except Exception:
                raise HTTPException(422, f"Multipart body 'meta' part is not valid JSON contents.")
            meta_index = i
            break
    if not meta:
        raise HTTPException(400, "Multipart body did not provide required 'meta' part.")
    subsystems = meta.get("subsystems", [])
    if not isinstance(subsystems, list) and len(subsystems) and all(isinstance(sub, dict) for sub in subsystems):
        raise HTTPException(400, "Multipart 'meta' content is missing or provided invalid 'subsystems' definition.")

    # parse other parts to populate consent subsystems entries in metadata
    known_ids = [subsystem.get("data_id") for subsystem in subsystems]
    known_ids = [_id for _id in known_ids if _id and isinstance(_id, str)]  # ignore extra metadata subsystems
    if not known_ids:
        raise HTTPException(400, "Multipart 'meta' content did not provide any subsystem with valid 'data_id' field.")
    if len(set(known_ids)) != len(known_ids):
        raise HTTPException(409, "Multipart 'meta' content specified subsystems with duplicate 'data_id' field.")
    found_ids = set()
    for i, part in enumerate(decoded_body.parts):
        if i == meta_index:
            continue
        c_id = part.headers.get(b"Content-ID")
        if not c_id:
            raise HTTPException(422, f"Multipart body part (index: {i}) did not provide required 'Content-ID' header.")
        c_id = c_id.decode("utf-8")
        for subsystem in subsystems:
            data_id = subsystem.get("data_id")
            if not data_id:
                continue
            if data_id == c_id:
                if c_id in found_ids:
                    raise HTTPException(409, (
                        f"Multipart body (index: {i}, Content-ID: {c_id}) "
                        f"has a duplicate Content-ID with another part."
                    ))
                found_ids.add(c_id)
                # apply updates
                desc = part.headers.get(b"Content-Description")
                if desc and not subsystem.get("data_description"):
                    subsystem["data_description"] = desc.decode("utf-8")
                c_type = part.headers.get(b"Content-Type", b"").decode("utf-8")
                if c_type and len(c_type.split("/")) == 2:
                    subsystem["media_type"] = c_type
                # NOTE:
                #   no conversion of type/format/encoding needed because data itself will not be saved
                #   this is stored only temporarily to generate the hash from it, which needs a plain string
                subsystem["data"] = part.text
                subsystem.pop("data_id")  # avoid later schema validation
                break
        else:
            raise HTTPException(422, (
                f"Multipart body part (index: {i}, Content-ID: {c_id}) "
                f"could not be matched against any subsystem 'data_id' from meta part contents."
            ))
    return meta
