import argparse
import uuid
import logging
import sys
from typing import TYPE_CHECKING
from urllib.parse import urlparse, urljoin

from flasgger import Swagger
from flask import Flask, jsonify, request

from blockchain import __meta__, __title__
from blockchain.database import DB_TYPES
from blockchain.impl import Blockchain
from blockchain.utils import asbool, get_logger

if TYPE_CHECKING:
    from blockchain.database import Database


class BlockchainWebApp(Flask):
    blockchain = None   # type: Blockchain
    node = None         # type: str
    db = None           # type: Database


# Instantiate the Node
app = BlockchainWebApp(__name__)
Swagger(
    app,
    merge=True, config={"openapi": "3.0.2", "specs_route": "/api"},
    template={
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


@app.route("/")
def frontpage():
    body = {
        "description": "Blockchain Node",
        "node": app.node,
        "links": [
            {"rel": "api", "href": urljoin(request.url, "/api")}
        ]
    }
    return jsonify(body), 200


@app.route("/mine", methods=["GET"])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = app.blockchain.last_block
    proof = app.blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    app.blockchain.new_transaction(
        sender="0",
        recipient=app.node,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = app.blockchain.hash(last_block)
    block = app.blockchain.new_block(proof, previous_hash)

    response = {
        "message": "New Block Forged",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
    }
    return jsonify(response), 200


@app.route("/transactions/new", methods=["POST"])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = {"sender": str, "recipient": str, "amount": int}
    if not all(k in values and isinstance(values[k], required[k]) for k in required):
        return "Missing values amongst: {}".format(required), 400

    # Create a new Transaction
    index = app.blockchain.new_transaction(values["sender"], values["recipient"], values["amount"])

    response = {"message": f"Transaction will be added to Block {index}"}
    return jsonify(response), 201


@app.route("/chain", methods=["GET"])
def full_chain():
    detail = asbool(request.args.get("detail"))
    response = {
        "chain": app.blockchain.json(detail=detail),
        "length": len(app.blockchain.blocks),
    }
    return jsonify(response), 200


@app.route("/nodes", methods=["GET"])
def list_nodes():
    return jsonify({"nodes": list(app.blockchain.nodes)}), 200


@app.route("/nodes/register", methods=["POST"])
def register_nodes():
    values = request.get_json()

    nodes = values.get("nodes")
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400

    for node in nodes:
        app.blockchain.register_node(node)

    response = {
        "message": "New nodes have been added",
        "total_nodes": list(app.blockchain.nodes),
    }
    return jsonify(response), 201


@app.route("/nodes/resolve", methods=["GET"])
def consensus():
    replaced = app.blockchain.resolve_conflicts()

    if replaced:
        response = {"message": "Our chain was replaced", "new_chain": app.blockchain.chain}
    else:
        response = {"message": "Our chain is authoritative", "chain": app.blockchain.chain}
    app.db.save_chain(app.blockchain)
    return jsonify(response), 200


class DatabaseTypeAction(argparse.Action):
    choices = list(DB_TYPES)

    def __call__(self, parser, namespace, values, option_string=None):
        if not isinstance(values, str):
            raise TypeError("Invalid database URI string")
        uri = urlparse(values)
        if uri.netloc:
            db_type = uri.scheme
            db_conn = uri.netloc
        else:
            if not uri.path.startswith("/"):
                raise ValueError("Database URI without scheme must be an absolute path: [{}]".format(uri))
            db_type = "file"
            db_conn = uri.path
        db_impl = DB_TYPES.get(db_type)
        if not db_impl:
            raise ValueError("Unknown database type: [{}]".format(db_type))
        setattr(namespace, self.dest, db_impl(db_conn))


def main():
    parser = argparse.ArgumentParser(prog="blockchain", description="Blockchain Node Web Application")
    parser.add_argument("-p", "--port", default=5000, type=int, help="port to listen on")
    parser.add_argument("-n", "--node", help="Unique identifier of the node. Generate one if omitted.")
    parser.add_argument("--db", "--database", default="file", action=DatabaseTypeAction,
                        help="Database to use. Formatted as [type://connection-detail].")

    log_args = parser.add_argument_group(title="Logger", description="Logging control.")
    level_args = log_args.add_mutually_exclusive_group()
    level_args.add_argument("-q", "--quiet", action="store_true", help="Disable logging except errors.")
    level_args.add_argument("-d", "--debug", action="store_true",
                            help="Debug level logging. This also enables error traceback outputs in responses.")
    args = parser.parse_args()

    # set full module config
    level = logging.DEBUG if args.debug else logging.ERROR if args.quiet else logging.ERROR
    logger = get_logger("blockchain", level=level)
    if level == logging.DEBUG:
        app.debug = True

    try:
        port = args.port
        app.db = args.db

        # Generate a globally unique address for this node
        app.node = args.node if args.node else str(uuid.uuid4()).replace("-", "")
        app.blockchain = app.db.load_chain()
        app.run(host="0.0.0.0", port=port)
    except Exception as exc:
        logger.error("Unhandled error: %s", exc, exc_info=exc)
        sys.exit(-1)


if __name__ == "__main__":
    main()
