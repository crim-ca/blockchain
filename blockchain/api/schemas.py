from marshmallow import Schema, fields, post_load, pre_dump
from marshmallow.validate import OneOf
from marshmallow_enum import EnumField

from blockchain.impl import ConsentAction, ConsentType


class OrderedSchema(Schema):
    class Meta:
        ordered = True


class Link(fields.Mapping):
    href = fields.URL()
    rel = fields.String()
    title = fields.String(required=False)


class FormatQuery(Schema):
    """
    Format of the generated output.
    """
    f = fields.String(
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
    Will synchronize external nodes if not already resolved.
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
    Force re-synchronization with external node references.
    """
    sync = fields.Boolean(
        required=False,
        allow_none=True,
        default=False,
        attribute="sync",
        description=__doc__.strip()
    )


class ResolveQuery(Schema):
    """
    Force consensus resolution with external node references.
    """
    resolve = fields.Boolean(
        required=False,
        allow_none=True,
        default=False,
        attribute="resolve",
        description=__doc__.strip()
    )


class Frontpage(OrderedSchema):
    description = fields.String()
    node = fields.UUID()
    links = fields.List(Link)


class GetChainSchema(Schema):
    validation = True
    parameters = [
        {"in": "query", "type": fields.Boolean(allow_none=True), "name": "detail", "required": False}
    ]


class ConsentActionField(EnumField):
    def __init__(self,
                 *args,
                 required=True,
                 **kwargs):
        super(ConsentActionField, self).__init__(
            ConsentAction,
            *args,
            by_value=False,
            required=required,
            **kwargs
        )


class ConsentTypeField(EnumField):
    def __init__(self,
                 *args,
                 required=True,
                 **kwargs):
        super(ConsentTypeField, self).__init__(
            ConsentType,
            *args,
            by_value=True,
            required=required,
            **kwargs
        )


class ConsentStatusField(fields.Boolean):
    def __init__(self,
                 *args,
                 required=True,
                 default=False,
                 description="Explicit granted or revoked consent status of the corresponding action.",
                 **kwargs):
        super(ConsentStatusField, self).__init__(
            *args,
            description=description,
            required=required,
            default=default,
            **kwargs,
        )


class ConsentExpireField(fields.DateTime):
    def __init__(self,
                 *args,
                 required=False,
                 default=None,
                 description=(
                    "Moment when the consent should be considered expired. "
                    "Revert back automatically to revoked consent when datetime is reached. "
                    "Consents never expire if unspecified, unless explicitly updated with revoked consent."
                 ),
                 **kwargs):
        super(ConsentExpireField, self).__init__(
            *args,
            description=description,
            required=required,
            default=default,
            **kwargs,
        )


class ConsentRequestBody(Schema):
    class Meta:
        attribute = "data"

    action = ConsentActionField(
        description="Action affected by the consent change."
    )
    expire = ConsentExpireField()
    consent = ConsentStatusField()


class ConsentSchema(OrderedSchema):
    id = fields.UUID()
    action = ConsentActionField(
        description="Action represented by this consent definition."
    )
    content = fields.Boolean(
        description="Indicates if consent is given by data owner."
    )
    expire = ConsentExpireField()
    created = fields.DateTime(required=True)
    type = ConsentTypeField(
        description="Details the last modification type that defined this consent definition."
    )


class TransactionSchema(Schema):
    pass


class BlockSchema(OrderedSchema):
    id = fields.UUID()
    index = fields.Integer()
    proof = fields.Integer()
    created = fields.DateTime()
    previous_hash = fields.String()
    transactions = fields.List(fields.Nested(TransactionSchema))
    consents = fields.List(fields.Nested(ConsentSchema))


class ChainSummary(OrderedSchema):
    id = fields.UUID()
    updated = fields.DateTime(description="Last moment the chain was updated by consensus resolution.")
    # blocks = fields.List # FIXME: UUID or Block based on query param


class ChainResponse(OrderedSchema):
    chain = fields.Nested(ChainSummary)
    length = fields.Integer(description="Length of the blockchain.")
    links = fields.List(Link)


class ChainBlockResponse(OrderedSchema):
    message = fields.String(description="Result of block detail listing.")
    chain = fields.UUID(description="Reference identifier of the chain.")
    block = fields.Nested(BlockSchema(), description="Block details.")


class ListConsentsResponse(OrderedSchema):
    message = fields.String(description="Result of consents represented in the blockchain.")
    updated = fields.DateTime(description="Last moment the chain was updated by consensus resolution.")
    outdated = fields.Boolean(description="Status indicating if a consent change was detected across the node network.")
    verified = fields.Boolean(description="Status indicating if latest consents were validated against other nodes.")
    changes = fields.List(fields.String(), description="Summary of all consent changes history applied over the chain.")
    consents = fields.List(fields.Nested(ConsentSchema), description="Latest resolved consents.")


class UpdateConsentResponse(OrderedSchema):
    message = fields.String(description="Result of the new consent block.")
    index = fields.Integer(description="Index of the new block in the chain.")
    transactions = fields.List(fields.Nested(TransactionSchema))
    consents = fields.List(fields.Nested(ConsentSchema), description="Consents applied within the new block.")
    proof = fields.Integer(description="Proof of work associated to the block.")
    previous_hash = fields.String(description="Hash of the previous block in the chain.")


class ChainSchema(OrderedSchema):
    id = fields.UUID()
    blocks = fields.List(fields.Nested(BlockSchema))


class NodeID(fields.UUID):
    pass


class ResolveChainResponse(OrderedSchema):
    message = fields.String(description="Result of the consensus resolution.")
    updated = fields.DateTime(description="Last moment the chain was updated by consensus resolution.")
    resolved = fields.Boolean(description="Indicates if any update was applied following resolution.")
    validated = fields.Boolean(description="Indicates if any other node was available for consensus.")
    nodes = fields.List(NodeID, description="Nodes that participated in validation of consensus resolution.")
    chain = fields.List(fields.Nested(BlockSchema, description="Blocks that form the resolved chain."))
