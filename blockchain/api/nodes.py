from urllib.parse import urljoin

from flask import Blueprint, jsonify, request, url_for
from flask import current_app as APP  # noqa


NODES = Blueprint("nodes", __name__, url_prefix="/nodes")


@NODES.route("/", methods=["GET"])
def list_nodes():
    links = []
    scope = NODES.name + "."
    for rule in APP.url_map.iter_rules():
        endpoint = rule.endpoint
        if endpoint.startswith(scope):
            rel = endpoint.split(".")[-1] if endpoint != request.endpoint else "self"
            links.append({"href": urljoin(request.url, url_for(endpoint)), "rel": rel})
    return jsonify({"nodes": list(APP.nodes), "links": links})


@NODES.route("/", methods=["POST"])
def register_nodes():
    values = request.get_json()
    nodes = values.get("nodes")
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        APP.nodes.add(node)
        for chain in APP.blockchains.values():
            chain.register_node(node)

    response = {
        "message": "New nodes have been added",
        "total_nodes": list(APP.nodes),
    }
    return jsonify(response), 201
