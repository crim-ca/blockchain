from flask import Blueprint, Response, request, url_for
from flask import current_app as APP  # noqa
from flask_apispec import doc
from flask_mako import render_template
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from blockchain.api.block import BLOCK_REF, get_block
from blockchain.api.chain import CHAIN_ID, get_chain, get_chain_links, view_consents
from blockchain.impl import ConsentChange
from blockchain.utils import get_links

if TYPE_CHECKING:
    from typing import List

    from blockchain import AnyUUID, Link

VIEWS = Blueprint("ui", __name__, url_prefix="/ui")


def get_chain_shortcuts(chain_id):
    # type: (AnyUUID) -> List[Link]
    """
    Obtain all UI shortcuts to other pages relevant for the given blockchain.
    """
    chain_id = str(chain_id)
    shortcuts = [
        {"rel": "consents", "href": url_for("ui.display_consents", chain_id=chain_id)},
    ]
    for link in shortcuts:
        link["href"] = urljoin(request.url, link["href"])
        link["title"] = link["rel"].capitalize()
    return shortcuts


@VIEWS.route("/", methods=["GET"])
@doc("Display shortcuts to other pages.", tags=["UI"])
def shortcut_navigate():
    links = get_links(VIEWS, self=False)
    for link in links:
        link["name"] = link["rel"].replace("_", " ").capitalize()
    data = {"links": links}
    return Response(render_template("ui/templates/view_shortcuts.mako", **data))


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
    return Response(render_template("ui/templates/view_chains.mako", **data))


@VIEWS.route(f"/chains/{CHAIN_ID}/blocks/${BLOCK_REF}", methods=["GET"])
@doc("Display block details within a blockchain.", tags=["Blocks", "UI"])
def view_block(chain_id, block_ref):
    chain = get_chain(chain_id)
    block = get_block(block_ref, chain)
    data = {"block": block.json(), "chain": chain.id}
    return Response(render_template("ui/templates/view_block.mako", **data))


@VIEWS.route(f"/{CHAIN_ID}/consents", methods=["GET"])
@doc("Display consents status of a given blockchain.", tags=["Consents", "UI"])
def display_consents(chain_id):
    data = view_consents(chain_id).json
    return Response(render_template("ui/templates/view_consents.mako", **data))
