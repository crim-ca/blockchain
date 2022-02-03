import os.path

from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi_mako import FastAPIMako  # noqa
from pydantic import UUID4

import blockchain
from blockchain import __meta__
from blockchain.api import schemas
from blockchain.api.chain import get_chain, get_chain_links, view_consents
from blockchain.impl import Blockchain
from blockchain.typedefs import AnyUUID, JSON
from blockchain.utils import get_links


VIEWS = APIRouter(prefix="/ui")
# APP must initialize itself with MAKO afterward since cannot import it here (circular imports)
MAKO = FastAPIMako()


def add_metadata(request: Request, data: Dict[str, Any]) -> Dict[str, Any]:
    data["node_shortcuts"] = []
    data["node_id"] = request.app.node.id
    data["node_url"] = request.app.node.url
    data["version"] = __meta__["version"]
    # generic CSS to applied on detected fields using 'get_styled_value' (see 'utils.mako')
    # right side should be one of many CSS classes defined in 'styles.css'
    data["styles"] = {
        "action": "enum code nowrap",
        "type": "enum code",
        "consent": "bool",
        "created": "date wrap",
        "expire": "date wrap",
        "data_type": "enum",
        "data_provider": "",
        "data_hash": "hash",
        "bool": "bool",
        "date": "date",
        "datetime": "datetime",
        "code": "code",
        "enum": "enum",
        "hash": "hash",
        "uuid": "uuid",
        "undefined": "undefined",
        "wrap": "wrap",
        "nowrap": "nowrap",
        "lowercase": "lowercase",
        "warning": "warning",
        "label": "label",
        "plain": "",
    }
    data["ui_shortcuts"] = get_ui_node_links(request)
    return data


def get_ui_node_links(request):
    """
    Obtains generic UI links combined with specific UI endpoints for the current node.
    """
    links = get_links(request, VIEWS, self=False)
    for link in links:
        if link["rel"] == "ui":
            link["title"] = "Node Network"
        else:
            link["title"] = link["rel"].replace("_", " ").capitalize()
    return links


def get_chain_shortcuts(request: Request, chain_id: AnyUUID) -> List[schemas.Link]:
    """
    Obtain all UI shortcuts to other pages relevant for the given blockchain.
    """
    chain_id = str(chain_id)
    shortcuts = [
        {"rel": "blocks", "href": request.url_for("view_blocks", chain_id=chain_id)},
        {"rel": "consents", "href": request.url_for("display_consents", chain_id=chain_id)},
    ]
    for link in shortcuts:
        link["href"] = urljoin(str(request.url), link["href"])
        link["title"] = link["rel"].capitalize()
    return shortcuts  # type: ignore


def get_chain_info(request: Request, chain: Blockchain, strip_shortcut: Optional[str] = None) -> JSON:
    """
    Obtain metadata details about a resolved chain ID for rendering in the UI.
    """
    chain_id = str(chain.id)
    shortcuts = get_chain_shortcuts(request, chain_id)
    if strip_shortcut is not None:
        strip_shortcut = strip_shortcut.capitalize()
        shortcuts = list(filter(lambda s: s["title"] != strip_shortcut, shortcuts))
    return {"count": len(chain.blocks), "chain": chain_id, "shortcuts": shortcuts}


@VIEWS.get(
    "/",
    tags=["UI"],
    summary="Display Node details, networks nodes and shortcuts to other pages.",
    response_class=HTMLResponse,
)
@MAKO.template("ui/templates/view_node.mako")
async def shortcut_navigate(request: Request):
    data = {"nodes": request.app.nodes}
    return add_metadata(request, data)


@VIEWS.get(
    "/chains",
    tags=["Chains", "UI"],
    summary="Display registered blockchains on the current node.",
    response_class=HTMLResponse,
    responses={
        200: {
            "description": "Blockchains registered in the current node."
        }
    },
)
@MAKO.template("ui/templates/view_chains.mako")
async def view_chains(request: Request):
    data = {
        "chains": [
            {
                "id": str(chain_id),
                "links": get_chain_links(request, chain_id),
                "shortcuts": get_chain_shortcuts(request, chain_id)
            } for chain_id in request.app.blockchains
        ]
    }
    for chain in data["chains"]:
        # replace "self" by "Chain"
        chain["links"][0]["rel"] = "Chain"
        chain["links"][0]["title"] = "Chain"
    return add_metadata(request, data)


@VIEWS.get(
    "/chains/{chain_id}/blocks",
    tags=["Blocks", "UI"],
    summary="Display block details within a blockchain.",
    response_class=HTMLResponse,
    responses={
        200: {
            "description": "List of block details in blockchain."
        }
    }
)
@MAKO.template("ui/templates/view_blocks.mako")
async def view_blocks(request: Request, chain_id: UUID4):
    chain = get_chain(request.app, chain_id)
    blocks = [block.json() for block in chain.blocks]
    data = {"blocks": blocks}
    data.update(get_chain_info(request, chain, strip_shortcut="blocks"))
    return add_metadata(request, data)


@VIEWS.get(
    "/{chain_id}/consents",
    tags=["Consents", "UI"],
    summary="Display consents status of a given blockchain.",
    response_class=HTMLResponse,
    responses={
        200: {
            "description": "Consents represented in the blockchain."
        }
    }
)
@MAKO.template("ui/templates/view_consents.mako")
async def display_consents(request: Request, chain_id: UUID4):
    chain = get_chain(request.app, chain_id)
    data = await view_consents(request, chain.id)
    data.update(get_chain_info(request, chain, strip_shortcut="consents"))
    data.update({
        "consent_fields": {
            "action": "Action",
            "consent": "Consent",
            "type": "Type",
            "created": "Created",
            "expire": "Expire"
        },
        "subsystem_fields": {
            "data_type": "Type",
            "data_description": "Description",
            "data_source": "Source",
            "data_provider": "Provider",
            "data_hash": "Hash",
            "media_type": "Media-Type",
            "metadata": "Extra Metadata",
        }
    })
    return add_metadata(request, data)
