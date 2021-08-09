import uuid
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import requests
from flask import Blueprint, abort, jsonify, request, url_for
from flask import current_app as APP  # noqa
from flask_apispec import doc, marshal_with, use_kwargs

from blockchain.api import schemas
from blockchain.impl import AttributeDict, Blockchain, ConsentChange
from blockchain.utils import get_logger

if TYPE_CHECKING:
    from typing import List, Optional, Tuple, Union

    from blockchain import AnyRef, AnyUUID, Link
    from blockchain.impl import Block, Node


LOGGER = get_logger(__name__)

CHAIN = Blueprint("chain", __name__, url_prefix="/chains")
CHAIN_ID = "<uuid:chain_id>"
BLOCK_REF = "<string:block_ref>"


def get_chain(chain_id, allow_missing=False):
    # type: (uuid.UUID) -> Optional[Blockchain]
    """
    Obtains the chain matching the UUID if it exists.

    :raises: chain cannot be found or reference is invalid.
    :returns: matched chain or None if allowed missing ones.
    """
    if chain_id not in APP.blockchains:
        if allow_missing:
            return None
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


def get_chain_links(chain_id):
    # type: (AnyUUID) -> List[Link]
    """
    Obtain all API links relevant for the blockchain.
    """
    chain_id = str(chain_id)
    links = [
        {"rel": "self", "href": url_for("chain.view_chain", chain_id=chain_id)},  # first position important
        # {"rel": "transaction", "href": url_for("chain.new_transaction", chain_id=chain_id)},  # only POST
        {"rel": "mine", "href": url_for("chain.mine", chain_id=chain_id)},
        {"rel": "blocks", "href": url_for("chain.list_blocks", chain_id=chain_id)},
        {"rel": "consensus", "href": url_for("chain.consensus", chain_id=chain_id)},
        {"rel": "consents", "href": url_for("chain.view_consents", chain_id=chain_id)},
    ]
    for link in links:
        link["href"] = urljoin(request.url, link["href"])
        link["title"] = link["rel"].capitalize()
    return links


def check_blockchain_exists(node, chain_id):
    # type: (Node, AnyUUID) -> bool
    """
    Verifies if a blockchain reference can be found on a remote node.

    If the reference can be found, the blockchain is initiated for
    """
    try:
        resp = requests.get(f"{node.url}/chains/{chain_id}", timeout=2)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        LOGGER.info("Node [%s] does not know blockchain [%s] for initial creation.", node, chain_id)
        return False
    if resp.status_code == 200:
        LOGGER.info("Node [%s] knows blockchain [%s] for initial creation.", node, chain_id)
        return True
    return False


@CHAIN.route("/", methods=["GET"])
@doc(description="Obtain list of available blockchains on this node.", tags=["Chains"])
@use_kwargs(schemas.ResolveQuery, location="query")
def list_chains(resolve=False):
    chains = set(APP.blockchains)
    str_chains = {str(chain) for chain in chains}
    new_chains = set()

    resolved_nodes = 0
    if resolve:
        LOGGER.info("Resolving missing chains with remote nodes...")
        for node in APP.nodes:
            if node.resolved:
                resolved_nodes += 1
                try:
                    resp = requests.get(f"{node.url}/chains?resolve=false", timeout=2)
                    node_chains = set(resp.json()["chains"])
                    new_chains |= node_chains - str_chains
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    LOGGER.info("Node [%s] did not answer to provide blockchains for initial creation.", node)
                    continue
        LOGGER.info("Found %s missing chains", len(new_chains))
        for chain in new_chains:
            consensus(chain_id=chain)

    chains = list(APP.blockchains)
    data = {
        "chains": chains,
        "total": len(chains),
        "resolved_query": resolve,
        "resolved_nodes": resolved_nodes,
        "resolved_chains": len(new_chains),
    }
    return jsonify(data)


@CHAIN.route(f"/{CHAIN_ID}", methods=["GET"])
@doc(description="Obtain the list of blocks that constitute a blockchain.", tags=["Chains"])
def view_chain(chain_id):
    chain = get_chain(chain_id)
    response = {
        "chain": chain.json(detail=False),
        "length": len(chain.blocks),
        "links": get_chain_links(chain_id)
    }
    return jsonify(response)


@CHAIN.route(f"/{CHAIN_ID}/blocks", methods=["GET"])
@doc(description="Obtain full details of blocks that constitute a blockchain.", tags=["Chains", "Blocks"])
@use_kwargs(schemas.DetailQuery, location="query")
def list_blocks(chain_id, detail=False):
    chain = get_chain(chain_id)
    blocks = list(chain.blocks) if detail else [block.id for block in chain.blocks]
    data = AttributeDict({"blocks": blocks, "length": len(blocks)})
    return jsonify(data.json())


@CHAIN.route(f"/{CHAIN_ID}/blocks/{BLOCK_REF}", methods=["GET"])
@doc(description="Obtain the details of a specific block within a blockchain.", tags=["Chains", "Blocks"])
def chain_block(chain_id, block_ref):
    chain = get_chain(chain_id)
    block = get_block(block_ref, chain)
    data = AttributeDict({"chain": chain.id, "block": block})
    return jsonify(data.json())


@CHAIN.route(f"/{CHAIN_ID}/mine", methods=["GET"])
@doc(description="Mine a blockchain to generate a new block.", tags=["Chains"])
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
    APP.db.save_chain(blockchain)

    data = AttributeDict({
        "message": "New Block Forged",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
    })
    return jsonify(data.json())


@CHAIN.route(f"/{CHAIN_ID}/transactions", methods=["POST"])
@doc(description="Create a new transaction on the blockchain.", tags=["Chains"])
def new_transaction(chain_id):
    values = request.get_json()

    # Check that the required fields are in the POST'ed data
    required = {"sender": str, "recipient": str, "amount": int}
    if not all(k in values and isinstance(values[k], required[k]) for k in required):
        return f"Missing values amongst: {required}", 400

    # Create a new Transaction
    index = get_chain(chain_id).new_transaction(values["sender"], values["recipient"], values["amount"])

    data = {"message": f"Transaction will be added to Block {index}"}
    response = jsonify(data)
    response.status_code = 201
    return response


@CHAIN.route(f"/{CHAIN_ID}/consents", methods=["GET"])
@doc("Obtain consents status of a given blockchain.", tags=["Chains", "Consents"])
def view_consents(chain_id):
    chain = get_chain(chain_id)
    history = ConsentChange.history(chain)
    consents = [consent.json() for consent in ConsentChange.latest(chain)]
    outdated = chain.verify_outdated(APP.nodes)
    message = "Consents history resolved and validated against all other nodes."
    if outdated is None:
        message = "Consents history resolved but could not be validated against other nodes."
    elif outdated:
        message = "Consents history resolved but is missing updates from other nodes."
    data = AttributeDict({
        "message": message,
        "updated": chain.last_block.created,
        "outdated": outdated if isinstance(outdated, bool) else False,
        "verified": outdated is not None,
        "changes": history,
        "consents": consents,
    })
    return jsonify(data.json())


@CHAIN.route(f"/{CHAIN_ID}/consents", methods=["POST"])
@doc(description="Create a new consent change to be registered on the blockchain.", tags=["Chains", "Consents"])
@use_kwargs(schemas.ConsentBody, location="json")
def update_consent(chain_id, action, consent, expire=None):
    # run the proof of work algorithm to get the next proof
    blockchain = get_chain(chain_id)
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_consent(
        action=action,
        expire=expire,
        consent=consent,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    APP.db.save_chain(blockchain)

    response = AttributeDict({
        "message": "New Block Forged",
        "index": block["index"],
        "transactions": block["transactions"],
        "consents": block["consents"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
    })
    return jsonify(response.json())


# FIXME: apply schema validation to fix invalid values
@CHAIN.route(f"/{CHAIN_ID}/resolve", methods=["GET"])
@doc(description="Resolve a blockchain with other registered nodes with consensus.", tags=["Chains", "Nodes"])
@marshal_with(schemas.ResolveChain, 200,
              description="Resolved blockchain following consensus with other nodes.", apply=False)
@marshal_with(schemas.ResolveChain, 201,
              description="Generated missing blockchain retrieved from other nodes.", apply=False)
def consensus(chain_id):
    blockchain = get_chain(chain_id, allow_missing=True)
    generated = False
    if not blockchain:
        # special case of "first pull" of an entirely missing blockchain reference locally, but available elsewhere
        # when node doesn't have any block yet (eg: just created node/chain), fetch full definition if possible
        if not APP.nodes:
            abort(404, f"Blockchain [{chain_id!s}] not found and cannot be resolved (no blockchain nodes available).")
        for node in APP.nodes:
            if check_blockchain_exists(node, chain_id):
                # setup blockchain, but resolve conflicts with consensus instead of initialization
                blockchain = Blockchain(id=chain_id, genesis_block=False)
                generated = True
                break
        if blockchain is None:
            abort(404, f"Blockchain [{chain_id!s}] not found and cannot be resolved from other blockchain nodes.")

    replaced, validated = blockchain.resolve_conflicts(APP.nodes)
    if generated:
        message = "Missing blockchain was generated from remote node match."
        APP.blockchains[chain_id] = blockchain  # apply resolved generation
    elif replaced:
        message = "Blockchain was replaced with resolved conflicts."
    else:
        message = "Blockchain is authoritative."
    data = AttributeDict({
        "description": message,
        "updated": blockchain.updated,
        "resolved": generated or replaced,
        "validated": bool(len(validated)),
        "nodes": [node.id for node in validated],
        "chain": blockchain.chain
    })
    code = 201 if generated else 200
    APP.db.save_chain(blockchain)
    return data.json(), code
