from flask import Blueprint, jsonify
from flask import current_app as APP  # noqa
from flask_apispec import doc

from blockchain.api.chain import BLOCK_REF, get_block

BLOCK = Blueprint("block", __name__, url_prefix="/blocks")


@BLOCK.route(f"/{BLOCK_REF}", methods=["GET"])
@doc(description="Obtain the details of a specific block across blockchains.", tags=["Blocks"])
def find_block(block_ref):
    # type: (AnyRef) -> APP.response_class
    block, chain = get_block(block_ref)
    return jsonify({"chain": str(chain.id), "block": block.json()})
