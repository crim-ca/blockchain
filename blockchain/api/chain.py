import uuid
from typing import TYPE_CHECKING, List, Optional, Tuple, Union
from urllib.parse import urljoin

import requests
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, UUID4

from blockchain import AnyRef, AnyUUID
from blockchain.api import schemas
from blockchain.impl import AttributeDict, Block, Blockchain, ConsentChange, Node
from blockchain.utils import get_logger

if TYPE_CHECKING:
    from blockchain.app import BlockchainWebApp

LOGGER = get_logger(__name__)

CHAIN = APIRouter(prefix="/chains")


def get_chain(app: "BlockchainWebApp", chain_id: UUID4, allow_missing: bool = False) -> Optional[Blockchain]:
    """
    Obtains the chain matching the UUID if it exists.

    :raises: chain cannot be found or reference is invalid.
    :returns: matched chain or None if allowed missing ones.
    """
    if chain_id not in app.blockchains:
        if allow_missing:
            return None
        raise HTTPException(404, f"Blockchain [{chain_id!s}] not found.")
    return app.blockchains[chain_id]


def get_block(app: "BlockchainWebApp",
              block_ref: AnyRef,
              chain: Blockchain = None,
              ) -> Union[Block, Tuple[Block, Blockchain]]:
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
            raise HTTPException(400, f"Block reference as numeric index out of range [0, {len(chain.blocks)}].")
        return chain.blocks[block_ref]
    try:
        block_ref = UUID4(block_ref)
    except (TypeError, ValueError):
        raise HTTPException(400, f"Block reference not a valid UUID [{block_ref!s}]")
    blockchains = [chain] if chain else app.blockchains.values()
    for chain_search in blockchains:
        for block in chain_search.blocks:
            if block.id == block_ref:
                return block if chain else (block, chain_search)
    raise HTTPException(404, f"Block reference UUID [{block_ref!s}] not found in chain.")


def get_chain_links(request: Request, chain_id: AnyUUID) -> List[schemas.Link]:
    """
    Obtain all API links relevant for the blockchain.
    """
    chain_id = str(chain_id)
    links = [
        # order important as employed for nicer display in UI
        {"rel": "self", "href": request.url_for("view_chain", chain_id=chain_id)},  # first position important
        {"rel": "blocks", "href": request.url_for("list_blocks", chain_id=chain_id)},
        {"rel": "consents", "href": request.url_for("view_consents", chain_id=chain_id)},
        {"rel": "consensus", "href": request.url_for("consensus", chain_id=chain_id)},
        # {"rel": "transaction", "href": url_for("chain.new_transaction", chain_id=chain_id)},  # only POST
        {"rel": "mine", "href": request.url_for("mine", chain_id=chain_id)},
    ]  # type: List[Dict[str, str]]
    for link in links:
        link["href"] = urljoin(str(request.url), link["href"])
        link["title"] = link["rel"].capitalize()
    return links


def check_blockchain_exists(node: Node, chain_id: AnyUUID) -> bool:
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


@CHAIN.get(
    "/",
    tags=["Chains"],
    summary="Obtain list of available blockchains on this node.",
    responses={
        200: {"description": "List of available blockchains on this node."}
    }
)
async def list_chains(request: Request, resolve: bool = False):
    chains = set(request.app.blockchains)
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

    chains = list(request.app.blockchains)
    data = {
        "chains": chains,
        "total": len(chains),
        "resolved_query": resolve,
        "resolved_nodes": resolved_nodes,
        "resolved_chains": len(new_chains),
    }
    return data


@CHAIN.get(
    "/{chain_id}",
    tags=["Chains"],
    summary="Obtain the list of blocks that constitute a blockchain.",
    response_model=schemas.ChainSummaryResponse,
    responses={
        200: {
            "description": "Summary of blocks that constitute a blockchain."
        }
    }
)
async def view_chain(request: Request, chain_id: UUID4):
    chain = get_chain(request.app, chain_id)
    data = {
        "chain": chain.data(detail=False),
        "length": len(chain.blocks),
        "links": get_chain_links(request, chain_id)
    }
    return data


@CHAIN.get(
    "/{chain_id}/blocks",
    tags=["Chains", "Blocks"],
    summary="Obtain full details of blocks that constitute a blockchain.",
    response_model=Union[schemas.ChainConsentsDetailedResponse, schemas.ChainConsentsSummaryResponse],
    responses={
        200: {
            "description": "Blocks that form the blockchain."
        }
    }
)
async def list_blocks(request: Request, chain_id: UUID4, detail: bool = schemas.DetailQuery(False)):
    chain = get_chain(request.app, chain_id)
    blocks = list(chain.blocks) if detail else [block.id for block in chain.blocks]
    data = AttributeDict({"blocks": blocks, "length": len(blocks)})
    return data


@CHAIN.get(
    "/{chain_id}/blocks/{block_ref}",
    summary="Obtain the details of a specific block within a blockchain.",
    tags=["Chains", "Blocks"],
    response_model=schemas.ChainBlockResponse,
    responses={
        200: {
            "description": "Detail of a block within a chain."
        }
    }
)
async def chain_block(request: Request, chain_id: UUID4, block_ref: AnyRef = schemas.BlockPathRef(...)):
    chain = get_chain(request.app, chain_id)
    block = get_block(request.app, block_ref, chain)
    data = AttributeDict({
        "message": "Listing of block details successful.",
        "chain": chain.id,
        "block": block
    })
    return data


@CHAIN.get(
    "/{chain_id}/mine",
    tags=["Chains"],
    summary="Mine a blockchain to generate a new block.",
    status_code=201,
    responses={
        201: {
            "description": "New block generated from mining blockchain."
        }
    }
)
async def mine(request: Request, chain_id: UUID4):
    # We run the proof of work algorithm to get the next proof...
    blockchain = get_chain(request.app, chain_id)
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=request.app.node,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    request.app.db.save_chain(blockchain)

    data = AttributeDict({
        "message": "New block forged.",
        "index": block["index"],
        "transactions": block["transactions"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
    })
    return data


@CHAIN.post(
    "/{chain_id}/transactions",
    tags=["Chains"],
    summary="Create a new transaction on the blockchain.",
    status_code=201,
    responses={
        201: {
            "description": "Transaction added to Block for insertion in chain."
        }
    }
)
async def new_transaction(request: Request, values: schemas.TransactionSchema, chain_id: UUID4):
    index = get_chain(request.app, chain_id).new_transaction(values["sender"], values["recipient"], values["amount"])
    data = {"message": f"Transaction will be added to Block {index}"}
    return data


@CHAIN.get(
    "/{chain_id}/consents",
    tags=["Chains", "Consents"],
    summary="Obtain latest consents status in the blockchain.",
    responses={
        200: {
            "description": "Latest consents in the blockchain.",
        }
    }
)
async def view_consents(request: Request, chain_id: UUID4):
    chain = get_chain(request.app, chain_id)
    history = ConsentChange.history(chain)
    consents = [consent.json() for consent in ConsentChange.latest(chain)]
    outdated = chain.verify_outdated(request.app.nodes)
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
    return data


@CHAIN.post(
    "/{chain_id}/consents", tags=["Chains", "Consents"],
    summary="Create a new consent change to be registered on the blockchain.",
    response_model=schemas.UpdateConsentResponse,
    status_code=201,
    responses={
        201: {
            "description": "Updated consents with new block in chain."
        }
    }
)
def update_consent(request: Request, body: schemas.ConsentRequestBody, chain_id: UUID4):
    # run the proof of work algorithm to get the next proof
    blockchain = get_chain(request.app, chain_id)
    last_block = blockchain.last_block
    proof = blockchain.proof_of_work(last_block)

    # receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_consent(
        action=body.action,
        expire=body.expire,
        consent=body.consent,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)
    request.app.db.save_chain(blockchain)

    data = AttributeDict({
        "message": "New block forged.",
        "index": block["index"],
        "transactions": block["transactions"],
        "consents": block["consents"],
        "proof": block["proof"],
        "previous_hash": block["previous_hash"],
    })
    return data


@CHAIN.get(
    "/{chain_id}/resolve",
    tags=["Chains", "Nodes"],
    summary="Resolve a blockchain with other registered nodes with consensus.",
    response_model=schemas.ResolveChainResponse,
    responses={
        200: {
            "description": "Resolved blockchain following consensus with other nodes."
        },
        201: {
            "description": "Generated missing blockchain retrieved from other nodes."
        }
    }
)
def consensus(request: Request, chain_id: UUID4):
    blockchain = get_chain(request.app, chain_id, allow_missing=True)
    generated = False
    if not blockchain:
        # special case of "first pull" of an entirely missing blockchain reference locally, but available elsewhere
        # when node doesn't have any block yet (eg: just created node/chain), fetch full definition if possible
        if not request.app.nodes:
            raise HTTPException(404, f"Blockchain [{chain_id!s}] not found and cannot be resolved (no blockchain nodes available).")
        for node in requset.app.nodes:
            if check_blockchain_exists(node, chain_id):
                # setup blockchain, but resolve conflicts with consensus instead of initialization
                blockchain = Blockchain(id=chain_id, genesis_block=False)
                generated = True
                break
        if blockchain is None:
            raise HTTPException(404, f"Blockchain [{chain_id!s}] not found and cannot be resolved from other blockchain nodes.")

    replaced, validated = blockchain.resolve_conflicts(request.app.nodes)
    if generated:
        message = "Missing blockchain was generated from remote node match."
        request.app.blockchains[chain_id] = blockchain  # apply resolved generation
    elif replaced:
        message = "Blockchain was replaced with resolved conflicts."
    else:
        message = "Blockchain is authoritative."
    data = AttributeDict({
        "message": message,
        "updated": blockchain.updated,
        "resolved": generated or replaced,
        "validated": bool(len(validated)),
        "nodes": [node.id for node in validated],
        "chain": blockchain.chain
    })
    code = 201 if generated else 200
    request.app.db.save_chain(blockchain)
    return data, code
