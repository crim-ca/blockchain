from fastapi import APIRouter, Request

from blockchain.api import schemas
from blockchain.api.chain import get_block
from blockchain.typedefs import AnyRef

BLOCK = APIRouter(prefix="/blocks")


@BLOCK.get(
    "/{block_ref}",
    tags=["Blocks"],
    summary="Obtain the details of a specific block across blockchains.",
    response_model=schemas.ChainBlockResponse,
    responses={
        200: {
            "description": "Block details."
        }
    }
)
async def find_block(request: Request, block_ref: AnyRef = schemas.BlockPathRef(...)):
    block, chain = get_block(request.app, block_ref)
    data = {
        "message": "Listing of block details successful.",
        "chain": chain.id,
        "block": block
    }
    return data
