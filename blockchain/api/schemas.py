from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Union

from fastapi import Path, Query
from pydantic import AnyUrl, BaseModel, Field, PositiveInt, UUID4, constr

from blockchain.impl import ChangeHistoryStatus, ConsentAction, ConsentType, DataType
from blockchain.typedefs import Mapping


VersionString = constr(regex="^[0-9]+.[0-9]+.[0-9]+$")


def BlockPathRef(*args, description="Block UUID or index in the chain.", **kwargs):  # noqa
    return Path(*args, description=description, **kwargs)


def DetailQuery(*args, description="Obtain detailed description of the represented items.", **kwargs):  # noqa
    return Query(*args, description=description, **kwargs)


def FormatQuery(*args,  # noqa
                description="Format specifier for the output representation (f/format interchangeable).",
                **kwargs):
    return Query(*args, description=description, **kwargs)


class HTTPErrorResponse(BaseModel):
    code: int
    name: str
    description: str
    messages: Optional[List[str]]


class Link(BaseModel):
    href: AnyUrl
    rel: str = Field(min_length=1)
    title: Optional[str]


class FrontpageResponse(BaseModel):
    message: str
    version: VersionString
    node: UUID4
    links: List[Link]


class NodeSchema(BaseModel):
    id: UUID4
    url: AnyUrl
    resolved: bool


class NodesResponse(BaseModel):
    nodes: Union[List[NodeSchema], List[AnyUrl]]
    links: List[Link]


class RegisterNodesBody(BaseModel):
    nodes: List[AnyUrl] = Field(description="Endpoints of nodes to register.", min_items=1)


class RegisterNodesResponse(BaseModel):
    message: str = Field(description="Result of the operation.")
    total: int = Field(description="Amount of nodes that can participate in consensus resolution.")


class SubSystemBase(BaseModel):
    data_type: DataType = Field(description="Category of the data which consents are applied onto.")
    data_description: Optional[str] = Field(description="Details providing more context about the consented data.")
    data_source: Optional[str] = Field(description="Provenance of the data (e.g.: URL, services, etc.).")
    data_provider: Optional[str] = Field(description="Data provider that generates the consents requirements.")
    metadata: Optional[Union[Mapping, str]] = Field(
        description="Additional metadata to be associated with the consents to better describe them."
    )


class SubSystemDataSubmitted(BaseModel):
    media_type: Optional[str] = Field(
        description="Explicit IANA data content format (defaults to plain/text or octets based on data if omitted)."
    )
    data: Union[bytes, str] = Field(
        description="Literal data that contents apply to for validation (not stored in blockchain)."
    )


class SubSystemRequestBody(SubSystemBase, SubSystemDataSubmitted):
    class Config:
        extra = "forbid"  # make sure to forbid 'data_hash' for example


class SubSystemDataResolved(BaseModel):
    media_type: str = Field(description="Specified or resolved IANA data content format.")
    data_hash: str = Field(description="Encrypted data representation of validation of associated consents.")


class SubSystemResponseBody(SubSystemBase, SubSystemDataResolved):
    pass


class ConsentRequestBody(BaseModel):
    action: ConsentAction
    consent: bool
    expire: Optional[datetime] = None
    subsystems: Optional[List[SubSystemRequestBody]] = Field(
        description="Subsystem definitions and metadata related to data with applied consents."
    )


class ConsentSchema(BaseModel):
    id: UUID4
    action: ConsentAction = Field(description="Action represented by this consent definition.")
    consent: bool = Field(description="Indicates if consent is given by data owner.")
    type: ConsentType = Field(description="Details the last modification type that defined this consent definition.")
    created: datetime
    expire: Optional[datetime] = Field(None, description=(
        "Moment when the consent should be considered expired. "
        "Revert back automatically to revoked consent when datetime is reached. "
        "Consents never expire if unspecified, unless explicitly updated with revoked consent."
    ))
    subsystems: List[SubSystemResponseBody] = Field(
        description="Subsystem definitions and metadata related to data with applied consents."
    )


class TransactionSchema(BaseModel):
    sender: str
    recipient: str
    amount: Decimal


class BlockSchema(BaseModel):
    id: UUID4
    index: int
    proof: int
    created: datetime
    previous_hash: str
    transactions: List[TransactionSchema]
    consents: List[ConsentSchema]


class ChainBlockResponse(BaseModel):
    message: str = Field(description="Result of block detail listing.")
    chain: UUID4
    block: BlockSchema


class ChainConsentsSummaryResponse(BaseModel):
    class Config:
        schema_extra = {
            "description": "Default summary representation."
        }
    blocks: List[UUID4]
    length: PositiveInt


class ChainConsentsDetailedResponse(BaseModel):
    class Config:
        schema_extra = {
            "description": "Detailed representation when query parameter requests it."
        }
    blocks: List[BlockSchema]
    length: PositiveInt


class Change(BaseModel):
    class Config:
        extra = "forbid"

    status: ChangeHistoryStatus = Field(description="Modification type that introduced consents change in the history.")
    detail: str = Field(description="Description of the consent change in the history.")
    action: Optional[ConsentAction] = Field(description="Applicable action that caused consent change in the history.")
    consent: Optional[bool] = Field(description="Allowed or revoked consent action that cause change in the history.")
    created: Optional[datetime] = Field(description="Creation datetime that caused consent change in the history.")
    expired: Optional[datetime] = Field(description="Expiration datetime that caused consent change in the history.")


class ListConsentsResponse(BaseModel):
    message: str = Field(description="Result of consents represented in the blockchain.")
    updated: datetime = Field(description="Last moment the chain was updated by consensus resolution.")
    outdated: bool = Field(description="Status indicating if a consent change was detected across the node network.")
    verified: bool = Field(description="Status indicating if latest consents were validated against other nodes.")
    summary: List[str] = Field(description="Summary of all consent changes history applied over the chain.")
    changes: List[Change] = Field(description="Detailed consent change history applied over the chain.")
    consents: List[ConsentSchema] = Field(description="Latest resolved consents.")


class UpdateConsentResponse(BaseModel):
    message: str = Field(description="Result of the new consent block.")
    index: PositiveInt = Field(description="Index of the new block in the chain.")
    transactions: List[TransactionSchema]
    consents: List[ConsentSchema] = Field(description="Consents applied within the new block.")
    proof: int = Field(description="Proof of work associated to the block.")
    previous_hash: str = Field(description="Hash of the previous block in the chain.")


class ChainSchema(BaseModel):
    id: UUID4
    updated: datetime = Field(description="Last moment the chain was updated by consensus resolution.")
    blocks: List[BlockSchema] = Field(min_items=1)


class ChainSummarySchema(BaseModel):
    id: UUID4
    updated: datetime = Field(description="Last moment the chain was updated by consensus resolution.")
    blocks: List[UUID4] = Field(min_items=1)


class ChainSummaryResponse(BaseModel):
    chain: ChainSummarySchema
    length: PositiveInt
    links: List[Link]


class ResolveChainResponse(BaseModel):
    message: str = Field(description="Result of the consensus resolution.")
    updated: datetime = Field(description="Last moment the chain was updated by consensus resolution.")
    resolved: bool = Field(description="Indicates if any update was applied following resolution.")
    validated: bool = Field(description="Indicates if any other node was available for consensus.")
    nodes: UUID4 = Field(description="Nodes that participated in validation of consensus resolution.")
    chain: List[BlockSchema] = Field(description="Blocks that form the resolved chain.")
