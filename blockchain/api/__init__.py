import os
import importlib
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from flask import Flask, Response, json, jsonify, request
from flask_mako import MakoTemplates
from flask_smorest import Api, Blueprint
from flask_smorest.arguments import ArgumentsMixin
from flask_smorest.response import ResponseMixin
from werkzeug.exceptions import HTTPException

from blockchain import __meta__, __title__
from blockchain.api import schemas
from blockchain.api.block import BLOCK
from blockchain.api.chain import CHAIN
from blockchain.api.nodes import NODES
from blockchain.ui.views import VIEWS

if TYPE_CHECKING:
    from typing import List

    from blockchain.database import Database
    from blockchain.impl import MultiChain, Node


class BlockchainWebApp(Flask, ArgumentsMixin, ResponseMixin):
    blockchains = None  # type: MultiChain
    nodes = None        # type: List[Node]  # list instead of set to preserve order
    node = None         # type: Node
    db = None           # type: Database
    secret = None       # type: str


# Instantiate the blockchain node webapp
APP = BlockchainWebApp(__name__)
MAIN = Blueprint("main", __name__)


@APP.errorhandler(HTTPException)
def handle_exception(error):
    # type: (HTTPException) -> Response
    """Return JSON instead of HTML for HTTP errors."""
    response = error.get_response()
    data = {
        "code": error.code,
        "name": error.name,
        "description": error.description,
    }
    exception = getattr(error, "exc", None)
    messages = getattr(exception, "messages", None)
    if messages:
        data["messages"] = messages
    response.data = json.dumps(data)
    response.content_type = "application/json"
    return response


@MAIN.route("/", methods=["GET"])
@MAIN.doc(summary="Details of this blockchain node.", tags=["API"])
@MAIN.response(200, schemas.Frontpage, description="Landing page of the Blockchain Node API.")
def frontpage():
    """
    Landing page of the Blockchain Node API.
    """
    body = {
        "message": "Blockchain Node",
        "node": APP.node.id,
        "version": __meta__["version"],
        "links": [
            {"rel": "api", "href": urljoin(request.url, "/api")},
            {"rel": "ui", "href": urljoin(request.url, "/ui")},
            {"rel": "json", "href": urljoin(request.url, "/schema")},
            {"rel": "yaml", "href": urljoin(request.url, "/schema?f=yaml")},
            {"rel": "nodes", "href": urljoin(request.url, "/nodes")},
            {"rel": "self", "href": request.url}
        ]
    }
    return body


@MAIN.route("/schema", methods=["GET"])
@MAIN.doc(description="Obtain the OpenAPI schema of supported requests.", tags=["API"])
@MAIN.arguments(schemas.FormatQuery, location="query")
@MAIN.response(200, description="OpenAPI schema definition.")
def openapi_schema(format=None):
    if format == "yaml":
        resp = Response(API.spec.to_yaml())
        resp.mimetype = "text/plain"
        return resp
    return API.spec.to_dict()


APP.config["JSON_SORT_KEYS"] = False
APP.config["OPENAPI_URL_PREFIX"] = "/api"
APP.config["OPENAPI_JSON_PATH"] = "/json"
APP.config["OPENAPI_REDOC_PATH"] = "/docs"
APP.register_blueprint(MAIN)
APP.register_blueprint(BLOCK)
APP.register_blueprint(CHAIN)
APP.register_blueprint(NODES)
APP.register_blueprint(VIEWS)
API = Api(APP, spec_kwargs={
    "title": __title__,
    "version": __meta__["Version"],
    "openapi_version": "3.0.2",
    "info": {
        "title": __title__,
        "description": __meta__["Summary"],
        "contact": {
            "responsibleOrganization": __meta__["Author"],
            "responsibleDeveloper": __meta__["Maintainer"],
            "email": __meta__["Maintainer-email"],
            "url": __meta__["Home-page"],  # url=... in setup
        },
        # "termsOfService": "http://me.com/terms",
        "license": __meta__["License"],
        "version": __meta__["Version"]
    }
})
