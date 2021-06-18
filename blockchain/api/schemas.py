from marshmallow import Schema, fields
from marshmallow.validate import OneOf

from blockchain.impl import ConsentAction


class Link(fields.Mapping):
    href = fields.URL()
    rel = fields.Str()


class FormatQuery(Schema):
    """
    Format of the generated output.
    """
    f = fields.Str(
        validate=OneOf(["json", "yaml"]),
        required=False,
        allow_none=True,
        default="json",
        attribute="format",
        description=__doc__.strip()
    )


class DetailQuery(Schema):
    """
    Detail representation the generated output.
    """
    detail = fields.Boolean(
        required=False,
        allow_none=True,
        default=False,
        attribute="detail",
        description=__doc__.strip()
    )


class SyncQuery(Schema):
    """
    Force sync of external references.
    """
    sync = fields.Boolean(
        required=False,
        allow_none=True,
        default=False,
        attribute="sync",
        description=__doc__.strip()
    )


class Frontpage(Schema):
    description = fields.Str()
    node = fields.UUID()
    links = fields.List(Link)


class GetChainSchema(Schema):
    validation = True
    parameters = [
        {"in": "query", "type": fields.Boolean(allow_none=True), "name": "detail", "required": False}
    ]


class ConsentBody(Schema):
    class Meta:
        attribute = "data"

    action = fields.Str(
        validate=OneOf([action.value for action in ConsentAction]),
        required=False,
        allow_none=True,
        default="json",
        attribute="format",
        description=__doc__.strip()
    )


class BlockSchema(fields.Mapping):
    id = fields.UUID()
    index = fields.Int()
    proof = fields.Int()
    created = fields.DateTime()
    previous_hash = fields.Str()
    # transactions =
    # consents =


class ChainSchema(fields.Mapping):
    id = fields.UUID()
    blocks = fields.List(BlockSchema)


class ResolveChain(Schema):
    description = fields.Str(description="Result of the consensus resolution.")
    updated = fields.DateTime(description="Last moment the chain was updated by consensus resolution.")
    resolved = fields.Boolean(description="Indicates if any update was applied following resolution.")
    validated = fields.Boolean(description="Indicates if any other node was available for consensus.")
    chain = fields.List(BlockSchema, description="Blocks that form the resolved chain.")
