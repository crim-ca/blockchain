import uuid
from typing import TYPE_CHECKING, TypeVar

from flask import Blueprint, abort, jsonify, request
from flask import current_app as APP  # noqa
from flask_apispec import doc, use_kwargs

from blockchain.api import schemas
from blockchain.utils import get_links

if TYPE_CHECKING:
    from blockchain import AnyRef
    from blockchain.impl import Node


NODES = Blueprint("nodes", __name__, url_prefix="/nodes")
NODE_REF = "<string:node_ref>"


def get_node(node_ref):
    # type: (AnyRef) -> Node
    """
    Searches for a block using any reference and optionally a chain.

    Limit search to only specific blockchain if provided.
    Index search allowed only when blockchain is specified.

    :raises: block cannot be found or reference is invalid.
    :returns: matched block, also returns the chain it was found in if not provided as input.
    """
    if str.isnumeric(node_ref):
        node_idx = int(node_ref)
        if node_idx < 0 or node_idx >= len(APP.nodes):
            abort(400, f"Node reference as numeric index out of range [0, {len(APP.nodes)}].")
        return APP.nodes[node_idx]
    try:
        node_ref = uuid.UUID(node_ref)
    except (TypeError, ValueError):
        abort(400, f"Node reference not a valid UUID [{node_ref!s}]")

    for node in APP.nodes:
        if node.id == node_ref:
            return node
    abort(404, f"Node reference UUID [{node_ref!s}] not found.")


@NODES.route("/", methods=["GET"])
@doc(description="Registered nodes which this blockchain node will resolve consensus against.", tags=["Nodes"])
@use_kwargs(schemas.DetailQuery, location="query")
@use_kwargs(schemas.SyncQuery, location="query")
def list_nodes(detail=False, sync=False):
    # type: (bool, bool) -> APP.response_class
    links = get_links(NODES)
    nodes = APP.nodes or []
    if sync:
        for node in nodes:
            node.sync_id()
    nodes = [node.json() if detail else node.url for node in nodes]
    return jsonify({"nodes": nodes, "links": links})


@NODES.route("/", methods=["POST"])
@doc(description="Register a new blockchain node to resolve consensus against.", tags=["Nodes"])
def register_nodes():
    # type: () -> APP.response_class
    values = request.get_json()
    endpoints = values.get("nodes")
    if endpoints is None:
        return "Error: Please supply a valid list of nodes", 400

    node_urls = [node.url for node in APP.nodes]
    for node_endpoint in endpoints:
        try:
            node = Node(node_endpoint)
        except Exception as exc:
            abort(400, str(exc))
        if node_endpoint in node_urls:
            abort(409, f"Node already registered: [{node_endpoint}]")
        APP.nodes.append(node)  # noqa
        for chain in APP.blockchains.values():
            chain.register_node(node)

    response = {
        "message": "New nodes have been added",
        "total": len(APP.nodes),
    }
    return jsonify(response), 201


@NODES.route(f"/{NODE_REF}", methods=["GET"])
@doc(description="Obtain synchronization details of a registered blockchain node.", tags=["Nodes"])
def view_node(node_ref):
    # type: (AnyRef) -> APP.response_class
    node = get_node(node_ref)
    return jsonify(node)
