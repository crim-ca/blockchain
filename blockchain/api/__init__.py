import importlib
import os
from typing import TYPE_CHECKING, List, Optional
from typing_extensions import Literal
from urllib.parse import urljoin

import yaml
from fastapi import APIRouter, Request, Response
from fastapi.encoders import jsonable_encoder
from pydantic import AnyUrl

from blockchain import __meta__
from blockchain.api import schemas
from blockchain.database import Database

# shortcuts for top-level app
from blockchain.api.block import BLOCK
from blockchain.api.chain import CHAIN
from blockchain.api.nodes import NODES
from blockchain.ui.views import MAKO, VIEWS

if TYPE_CHECKING:
    from blockchain.app import BlockchainWebApp

MAIN = APIRouter()


@MAIN.get(
    "/",
    tags=["API"],
    summary="Details of this blockchain node.",
    response_model=schemas.FrontpageResponse,
    responses={
        200: {
            "description": "Landing page of the Blockchain Node API."
        }
    }
)
async def frontpage(request: Request):
    """
    Landing page of the Blockchain Node API.
    """
    base = str(request.url)
    body = {
        "message": "Blockchain Node",
        "node": request.app.node.id,
        "version": __meta__["version"],
        "links": [
            {"rel": "api", "title": "OpenAPI documentation.", "href": urljoin(base, "/api")},
            {"rel": "json", "title": "OpenAPI schemas (JSON).", "href": urljoin(base, "/schema")},
            {"rel": "yaml", "title": "OpenAPI schemas (YAML).", "href": urljoin(base, "/schema?f=yaml")},
            {"rel": "ui", "title": "User interface.", "href": urljoin(base, "/ui")},
            {"rel": "nodes", "title": "Registered network nodes.", "href": urljoin(base, "/nodes")},
            {"rel": "self", "title": "API entrypoint.", "href": base}
        ]
    }
    return body


@MAIN.get("/schema", tags=["API"], responses={
    200: {
        "description": "Obtain the OpenAPI schema of supported requests.",
        "content": {
            "application/json": {
                "schema": {
                    "$ref": "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/3.0.3/schemas/v3.0/schema.json"
                }
            },
            "text/plain": {
               "schema": {
                   "$ref": "https://raw.githubusercontent.com/OAI/OpenAPI-Specification/3.0.3/schemas/v3.0/schema.yaml"
               }
            }
        }
    }
})
async def openapi_schema(
    request: Request,
    f: Optional[Literal["json", "yaml"]] = schemas.FormatQuery(None),
    format: Literal["json", "yaml"] = schemas.FormatQuery("json"),
):
    app = request.app  # type: "BlockchainWebApp"
    oas = app.openapi()
    if (f or format) == "yaml":
        data = jsonable_encoder(oas)
        # FIXME: patch contact URL (https://github.com/tiangolo/fastapi/issues/1071)
        data["info"]["contact"]["url"] = str(data["info"]["contact"]["url"])
        text = yaml.safe_dump(data)
        resp = Response(text, media_type="text/plain; charset=utf-8")
        return resp
    return oas
