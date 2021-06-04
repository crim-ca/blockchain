from flask import Blueprint, jsonify
from flask import current_app as APP  # noqa

from blockchain.api.chain import BLOCK_REF, get_block

BLOCK = Blueprint("block", __name__, url_prefix="/blocks")


@BLOCK.route(f"/{BLOCK_REF}", methods=["GET"])
def find_block(block_ref):
    block, chain = get_block(block_ref)
    return jsonify({"chain": str(chain.id), "block": block.json()})
