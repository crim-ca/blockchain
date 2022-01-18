import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Request

from blockchain import AnyRef
from blockchain.api import schemas
from blockchain.impl import Node
from blockchain.utils import get_links

if TYPE_CHECKING:
    from blockchain.app import BlockchainWebApp

NODES = APIRouter(prefix="/nodes")


def get_node(app: "BlockchainWebApp", node_ref: AnyRef) -> Node:
    """
    Searches for a block using any reference and optionally a chain.

    Limit search to only specific blockchain if provided.
    Index search allowed only when blockchain is specified.

    :raises: block cannot be found or reference is invalid.
    :returns: matched block, also returns the chain it was found in if not provided as input.
    """
    if str.isnumeric(node_ref):
        node_idx = int(node_ref)
        if node_idx < 0 or node_idx >= len(app.nodes):
            raise HTTPException(400, f"Node reference as numeric index out of range [0, {len(app.nodes)}].")
        return app.nodes[node_idx]
    try:
        node_ref = uuid.UUID(node_ref)
    except (TypeError, ValueError):
        raise HTTPException(400, f"Node reference not a valid UUID [{node_ref!s}]")

    for node in app.nodes:
        if node.id == node_ref:
            return node
    raise HTTPException(404, f"Node reference UUID [{node_ref!s}] not found.")


@NODES.get(
    "/",
    tags=["Nodes"],
    summary="Obtain other nodes known by this node for consensus resolution.",
    response_model=schemas.NodesResponse,
    responses={
        200: {
            "description": "Registered nodes which this blockchain node will resolve consensus against."
        }
    }
)
async def list_nodes(request: Request, detail=False, sync=False):
    links = get_links(request, NODES)
    nodes = request.app.nodes or []
    if sync:
        for node in nodes:
            node.sync_id()
    nodes = [node.json() if detail else node.url for node in nodes]
    return {"nodes": nodes, "links": links}


@NODES.post(
    "/",
    tags=["Nodes"],
    summary="Register a new blockchain node to resolve consensus against.",
    status_code=201,
    response_model=schemas.RegisterNodesResponse,
    responses={
        201: {
            "description": "Description of the registered node."
        }
    }
)
def register_nodes(request: Request, body: schemas.RegisterNodesBody):
    app = request.app
    endpoints = body.get("nodes")
    if endpoints is None:
        return "Error: Please supply a valid list of nodes", 400

    node_urls = [node.url for node in app.nodes]
    for node_endpoint in endpoints:
        try:
            node = Node(node_endpoint)
        except Exception as exc:
            raise HTTPException(400, str(exc))
        if node_endpoint in node_urls:
            raise HTTPException(409, f"Node already registered: [{node_endpoint}]")
        app.nodes.append(node)  # noqa
        for chain in app.blockchains.values():
            chain.register_node(node)

    data = {
        "message": "New nodes have been added.",
        "total": len(app.nodes),
    }
    return data


@NODES.get(
    "/{node_ref}",
    tags=["Nodes"],
    summary="Obtain synchronization details of a registered blockchain node.",
    responses={
        200: {
            "description": "Synchronization details of blockchain node."
        }
    }
)
async def view_node(request: Request, node_ref: AnyRef):
    node = get_node(request.app, node_ref)
    return node
