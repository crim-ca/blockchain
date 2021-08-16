from flask import Blueprint, Response, request, url_for
from flask import current_app as APP  # noqa
from flask_apispec import doc
from flask_mako import render_template
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from blockchain import __meta__
from blockchain.api.chain import CHAIN_ID, get_chain, get_chain_links, view_consents
from blockchain.utils import get_links

if TYPE_CHECKING:
    from typing import List, Optional

    from blockchain import AnyUUID, Link, JSON
    from blockchain.impl import Blockchain

VIEWS = Blueprint("ui", __name__, url_prefix="/ui")


def render_template_meta(template, **data):
    data["node_id"] = APP.node.id
    data["node_url"] = APP.node.url
    data["version"] = __meta__["version"]
    return render_template(template, **data)


def get_chain_shortcuts(chain_id):
    # type: (AnyUUID) -> List[Link]
    """
    Obtain all UI shortcuts to other pages relevant for the given blockchain.
    """
    chain_id = str(chain_id)
    shortcuts = [
        {"rel": "blocks", "href": url_for("ui.view_blocks", chain_id=chain_id)},
        {"rel": "consents", "href": url_for("ui.display_consents", chain_id=chain_id)},
    ]
    for link in shortcuts:
        link["href"] = urljoin(request.url, link["href"])
        link["title"] = link["rel"].capitalize()
    return shortcuts


def get_chain_info(chain, strip_shortcut=None):
    # type: (Blockchain, Optional[str]) -> JSON
    """
    Obtain metadata details about a resolved chain ID for rendering in the UI.
    """
    chain_id = str(chain.id)
    shortcuts = get_chain_shortcuts(chain_id)
    if strip_shortcut is not None:
        strip_shortcut = strip_shortcut.capitalize()
        shortcuts = list(filter(lambda s: s["title"] != strip_shortcut, shortcuts))
    return {"count": len(chain.blocks), "chain": chain_id, "shortcuts": shortcuts}


@VIEWS.route("/", methods=["GET"])
@doc("Display shortcuts to other pages.", tags=["UI"])
def shortcut_navigate():
    links = get_links(VIEWS, self=False)
    for link in links:
        link["title"] = link["rel"].replace("_", " ").capitalize()
    data = {"links": links, "nodes": APP.nodes}
    return Response(render_template_meta("ui/templates/view_shortcuts.mako", **data))


@VIEWS.route("/chains", methods=["GET"])
@doc("Display registered blockchains on the current node.", tags=["Chains", "UI"])
def view_chains():
    data = {
        "chains": [
            {
                "id": str(chain_id),
                "links": get_chain_links(chain_id),
                "shortcuts": get_chain_shortcuts(chain_id)
            } for chain_id in APP.blockchains
        ]
    }
    for chain in data["chains"]:
        # replace "self" by "Chain"
        chain["links"][0]["rel"] = "Chain"
        chain["links"][0]["title"] = "Chain"
    return Response(render_template_meta("ui/templates/view_chains.mako", **data))


@VIEWS.route(f"/chains/{CHAIN_ID}/blocks", methods=["GET"])
@doc("Display block details within a blockchain.", tags=["Blocks", "UI"])
def view_blocks(chain_id):
    chain = get_chain(chain_id)
    blocks = [block.json() for block in chain.blocks]
    data = {"blocks": blocks}
    data.update(get_chain_info(chain, strip_shortcut="blocks"))
    return Response(render_template_meta("ui/templates/view_blocks.mako", **data))


@VIEWS.route(f"/{CHAIN_ID}/consents", methods=["GET"])
@doc("Display consents status of a given blockchain.", tags=["Consents", "UI"])
def display_consents(chain_id):
    chain = get_chain(chain_id)
    data = view_consents(chain.id).json
    data.update(get_chain_info(chain, strip_shortcut="consents"))
    return Response(render_template_meta("ui/templates/view_consents.mako", **data))
