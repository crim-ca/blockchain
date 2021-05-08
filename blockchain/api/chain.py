from flask import Blueprint, jsonify, request
from flask import current_app as APP  # noqa


CHAIN = Blueprint("chain", __name__)


@CHAIN.route("/mine", methods=["GET"])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = APP.blockchain.last_block
    proof = APP.blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    APP.blockchain.new_transaction(
        sender="0",
        recipient=APP.node,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = APP.blockchain.hash(last_block)
    block = APP.blockchain.new_block(proof, previous_hash)

    response = {
        "message": "New Block Forged",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
    }
    return jsonify(response), 200


@CHAIN.route("/transactions/new", methods=["POST"])
def new_transaction():
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = {"sender": str, "recipient": str, "amount": int}
    if not all(k in values and isinstance(values[k], required[k]) for k in required):
        return "Missing values amongst: {}".format(required), 400

    # Create a new Transaction
    index = APP.blockchain.new_transaction(values["sender"], values["recipient"], values["amount"])

    response = {"message": f"Transaction will be added to Block {index}"}
    return jsonify(response), 201


@CHAIN.route("/chain", methods=["GET"])
def full_chain(query=None):
    response = {
        "chain": APP.blockchain.json(detail=False),
        "length": len(APP.blockchain.blocks),
    }
    return jsonify(response), 200
