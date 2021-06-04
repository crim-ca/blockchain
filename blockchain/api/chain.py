import uuid
from typing import TYPE_CHECKING

from flask import Blueprint, abort, jsonify, request
from flask import current_app as APP  # noqa

if TYPE_CHECKING:
    from typing import Tuple, Union

    from blockchain.impl import Block, Blockchain

    AnyRef = Union[str, uuid.UUID, int]


CHAIN = Blueprint("chain", __name__, url_prefix="/chains")
CHAIN_ID = "<uuid:chain_id>"
BLOCK_REF = "<string:block_ref>"


def get_chain(chain_id):
    # type: (uuid.UUID) -> Blockchain
    """
    Obtains the chain matching the UUID if it exists.

    :raises: chain cannot be found or reference is invalid.
    :returns: matched chain.
    """
    if chain_id not in APP.blockchains:
        abort(404, f"Blockchain [{chain_id!s}] not found.")
    return APP.blockchains[chain_id]


def get_block(block_ref, chain=None):
    # type: (AnyRef, Blockchain) -> Union[Block, Tuple[Block, Blockchain]]
    """
    Searches for a block using any reference and optionally a chain.

    Limit search to only specific blockchain if provided.
    Index search allowed only when blockchain is specified.

    :raises: block cannot be found or reference is invalid.
    :returns: matched block, also returns the chain it was found in if not provided as input.
    """
    if chain and str.isnumeric(block_ref):
        block_ref = int(block_ref)
        if block_ref < 0 or block_ref >= len(chain.blocks):
            abort(400, f"Block reference as numeric index out of range [0, {len(chain.blocks)}].")
        return chain.blocks[block_ref]
    try:
        block_ref = uuid.UUID(block_ref)
    except (TypeError, ValueError):
        abort(400, f"Block reference not a valid UUID [{block_ref!s}]")
    blockchains = [chain] if chain else APP.blockchains.values()
    for chain_search in blockchains:
        for block in chain_search.blocks:
            if block.id == block_ref:
                return block if chain else (block, chain_search)
    abort(404, f"Block reference UUID [{block_ref!s}] not found in chain.")


@CHAIN.route("/", methods=["GET"])
def list_chains():
    chains = list(APP.blockchains)
    return jsonify({"chains": chains, "total": len(chains)})


@CHAIN.route(f"/{CHAIN_ID}/mine", methods=["GET"])
def mine(chain_id):
    # We run the proof of work algorithm to get the next proof...
    blockchain = get_chain(chain_id)
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=APP.node,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        "message": "New Block Forged",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
    }
    return jsonify(response), 200


@CHAIN.route(f"/{CHAIN_ID}/transactions", methods=["POST"])
def new_transaction(chain_id):
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = {"sender": str, "recipient": str, "amount": int}
    if not all(k in values and isinstance(values[k], required[k]) for k in required):
        return f"Missing values amongst: {required}", 400

    # Create a new Transaction
    index = get_chain(chain_id).new_transaction(values["sender"], values["recipient"], values["amount"])

    response = {"message": f"Transaction will be added to Block {index}"}
    return jsonify(response), 201


@CHAIN.route(f"/{CHAIN_ID}", methods=["GET"])
def view_chain(chain_id):
    chain = get_chain(chain_id)
    response = {
        "chain": chain.json(detail=False),
        "length": len(chain.blocks),
    }
    return jsonify(response), 200


@CHAIN.route(f"/{CHAIN_ID}/blocks", methods=["GET"])
def list_blocks(chain_id):
    chain = get_chain(chain_id)
    return jsonify({"blocks": list(chain.blocks), "length": len(chain.blocks)})


@CHAIN.route(f"/{CHAIN_ID}/blocks/{BLOCK_REF}", methods=["GET"])
def chain_block(chain_id, block_ref):
    chain = get_chain(chain_id)
    block = get_block(block_ref, chain)
    return jsonify({"chain": chain.id, "block": block})


@CHAIN.route(f"/{CHAIN_ID}/resolve", methods=["GET"])
def consensus(chain_id):
    blockchain = get_chain(chain_id)
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {"message": "Our chain was replaced", "new_chain": blockchain.chain}
    else:
        response = {"message": "Our chain is authoritative", "chain": blockchain.chain}
    APP.db.save_chain(blockchain)
    return jsonify(response), 200
