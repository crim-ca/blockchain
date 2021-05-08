from marshmallow import Schema, fields
from marshmallow.validate import OneOf


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


class Frontpage(Schema):
    description = fields.Str()
    node = fields.UUID()
    links = fields.List(Link)


class GetChainSchema(Schema):
    validation = True
    parameters = [
        {"in": "query", "type": fields.Boolean(allow_none=True), "name": "detail", "required": False}
    ]
