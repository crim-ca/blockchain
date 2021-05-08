from typing import TYPE_CHECKING
from urllib.parse import urljoin

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask, Response, jsonify, request
from flask_apispec import FlaskApiSpec, doc, marshal_with, use_kwargs

from blockchain import __meta__, __title__
from blockchain.api import schemas
from blockchain.api.chain import CHAIN
from blockchain.api.nodes import NODES
from blockchain.impl import Blockchain

if TYPE_CHECKING:
    from blockchain.database import Database


class BlockchainWebApp(Flask):
    blockchain = None   # type: Blockchain
    node = None         # type: str
    url = None          # type: str
    db = None           # type: Database


# Instantiate the blockchain node webapp
APP = BlockchainWebApp(__name__)
APP.url_map.strict_slashes = False  # allow trailing slashes
APP.config["JSON_SORT_KEYS"] = False


@APP.route("/", methods=["GET"])
@marshal_with(schemas.Frontpage, 200, description="Landing page of the Blockchain Node API.")
def frontpage():
    """
    Landing page of the Blockchain Node API.
    """
    body = {
        "description": "Blockchain Node",
        "node": APP.node,
        "links": [
            {"rel": "api", "href": urljoin(request.url, "/api")},
            {"rel": "json", "href": urljoin(request.url, "/schema")},
            {"rel": "yaml", "href": urljoin(request.url, "/schema?f=yaml")},
            {"rel": "nodes", "href": urljoin(request.url, "/nodes")},
            {"rel": "self", "href": request.url}
        ]
    }
    return jsonify(body), 200


@APP.route("/schema", methods=["GET"])
@use_kwargs(schemas.FormatQuery, location="query")
@marshal_with(None, 200, description="OpenAPI schema definition.")
def openapi_schema(format=None):
    if format == "yaml":
        resp = Response(API.spec.to_yaml())
        resp.mimetype = "text/plain"
        return resp
    return jsonify(API.spec.to_dict())


APP.config.update({
    "APISPEC_SWAGGER_URL": "/json",
    "APISPEC_SWAGGER_UI_URL": "/api",
    "APISPEC_SPEC": APISpec(
        title=__title__,
        version=__meta__["Version"],
        openapi_version="3.0.2",
        plugins=[MarshmallowPlugin()],
        **{
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
        }
    )
})
APP.register_blueprint(CHAIN)
APP.register_blueprint(NODES)
API = FlaskApiSpec(APP)
API.register_existing_resources()
