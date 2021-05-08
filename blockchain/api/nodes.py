from urllib.parse import urljoin

from flask import Blueprint, jsonify, request, url_for
from flask import current_app as APP  # noqa


NODES = Blueprint("nodes", __name__, url_prefix="/nodes")


@NODES.route("/", methods=["GET"])
def nodes_links():
    links = []
    scope = NODES.name + "."
    for rule in APP.url_map.iter_rules():
        endpoint = rule.endpoint
        if endpoint.startswith(scope):
            rel = endpoint.split(".")[-1] if endpoint != request.endpoint else "self"
            links.append({"href": urljoin(request.url, url_for(endpoint)), "rel": rel})
    return jsonify({"links": links})


@NODES.route("/members", methods=["GET"])
def list_nodes():
    return jsonify({"nodes": list(APP.blockchain.nodes)}), 200


@NODES.route("/register", methods=["POST"])
def register_nodes():
    values = request.get_json()
    nodes = values.get("nodes")
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        APP.blockchain.register_node(node)

    response = {
        "message": "New nodes have been added",
        "total_nodes": list(APP.blockchain.nodes),
    }
    return jsonify(response), 201


@NODES.route("/resolve", methods=["GET"])
def consensus():
    replaced = APP.blockchain.resolve_conflicts()

    if replaced:
        response = {"message": "Our chain was replaced", "new_chain": APP.blockchain.chain}
    else:
        response = {"message": "Our chain is authoritative", "chain": APP.blockchain.chain}
    APP.db.save_chain(APP.blockchain)
    return jsonify(response), 200
