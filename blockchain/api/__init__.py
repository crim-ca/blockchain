import os
import importlib
from typing import List, Optional
from typing_extensions import Literal
from urllib.parse import urljoin

from fastapi import APIRouter, Request

from blockchain import __meta__
from blockchain.api import schemas
from blockchain.database import Database

# shortcuts for top-level app
from blockchain.api.block import BLOCK
from blockchain.api.chain import CHAIN
from blockchain.api.nodes import NODES
from blockchain.ui.views import MAKO, VIEWS

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
            {"rel": "api", "href": urljoin(base, "/api")},
            {"rel": "ui", "href": urljoin(base, "/ui")},
            {"rel": "json", "href": urljoin(base, "/schema")},
            {"rel": "yaml", "href": urljoin(base, "/schema?f=yaml")},
            {"rel": "nodes", "href": urljoin(base, "/nodes")},
            {"rel": "self", "href": base}
        ]
    }
    return body


@MAIN.get("/schema", tags=["API"], responses={
    200: {
        "description": "Obtain the OpenAPI schema of supported requests."
    }
})
async def openapi_schema(format: Literal["json", "yaml"] = "json"):
    if format == "yaml":
        resp = Response(API.spec.to_yaml())
        resp.mimetype = "text/plain"
        return resp
    return API.spec.to_dict()
