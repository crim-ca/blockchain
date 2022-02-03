import abc
import hashlib
import json
import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple, Union
from urllib.parse import urlparse

import magic
import requests
from dateutil import parser as dt_parser
from addict import Dict as AttributeDict  # auto generates attribute, properties and getter/setter dynamically

from blockchain.typedefs import AnyUUID, JSON, Mapping
from blockchain.utils import compute_hash, get_logger

LOGGER = get_logger(__name__)

# https://www.iana.org/assignments/media-types/media-types.xhtml
KNOWN_MEDIA_TYPES = frozenset([
    "application",
    "audio",
    "font",
    "example",
    "image",
    "message",
    "model",
    "multipart",
    "text",
    "video",
])


class Base(AttributeDict, abc.ABC):
    """
    Dictionary with extended attributes auto-``getter``/``setter`` for convenience.
    Explicitly overridden ``getter``/``setter`` attributes are called instead of ``dict``-key ``get``/``set``-item
    to ensure corresponding checks and/or value adjustments are executed before applying it to the sub-``dict``.
    """

    __json__ = True  # repr as JSON

    def __init__(self, *_, **kwargs):
        items = dict(*_)
        _id = items.pop("id", kwargs.pop("id", uuid.uuid4())) or uuid.uuid4()  # enforce generation if None/missing
        kwargs.update(items)
        kwargs.update({"id": uuid.UUID(str(_id))})
        super(Base, self).__init__(**kwargs)

    def __str__(self):
        # type: () -> str
        return f"{type(self).__name__} <{self.id}>"

    def __setattr__(self, name, value):
        prop = getattr(self.__class__, name, None)
        # default behavior ignores setter property, so allow it
        if isinstance(prop, property) and getattr(prop, "fset", None) is not None:
            self[name] = value
        else:
            super(Base, self).__setattr__(name, value)

    # FIXME: remove when integrated (https://github.com/mewwts/addict/pull/139)
    def __repr__(self):
        if self.__json__:
            cls = type(self)
            try:
                repr_ = json.dumps(self.json(force=False), indent=2, ensure_ascii=False)
            except Exception:  # noqa
                return dict.__repr__(self)
            return f"{cls.__module__}.{cls.__name__}\n{repr_}"
        return dict.__repr__(self)

    # FIXME: remove when integrated (https://github.com/mewwts/addict/pull/139)
    def json(self, force=True) -> JSON:
        """
        JSON representation of the data.
        """
        base = {}
        for key, value in self.items():
            key = str(key)  # ensure conversion
            if isinstance(value, (type(self), dict)):
                base[key] = AttributeDict(value).json()
            elif isinstance(value, (list, tuple)):
                base[key] = list(
                    (AttributeDict(item).json() if callable(item.json) else AttributeDict(item).json)
                    if isinstance(item, (type(self), dict)) or hasattr(item, "json")
                    else item
                    if isinstance(item, (int, float, bool, str, type(None)))
                    else str(item) if force else item
                    for item in value)
            elif isinstance(value, (int, float, bool, str, type(None))):
                base[key] = value
            elif hasattr(value, "json"):
                base[key] = value.json() if callable(value.json) else value.json
            else:
                base[key] = str(value) if force else value
        return base

    def params(self) -> Dict[str, Any]:
        """
        Obtain the internal data representation for storage.
        """
        return dict(self)


class WithDatetime(Base):
    def __init__(self, *args, **kwargs):
        # generate or set created datetime
        created = kwargs.pop("created", kwargs.pop("timestamp", None))
        Base.__setattr__(self, "created", created or self.created)
        super(WithDatetime, self).__init__(*args, **kwargs)

    @property
    def created(self) -> datetime:
        dt = self.get("created")
        if dt is None:
            dt = datetime.utcnow().isoformat()
            self["created"] = dt
        return dt

    @created.setter
    def created(self, created: Optional[Union[str, datetime]]) -> None:
        if created is not None and isinstance(created, str):
            created = datetime.fromisoformat(created)
        Base.__setitem__(self, "created", created)


class Transaction(Base):
    pass


class EnumNameHyphenCase(Enum):
    def _generate_next_value_(self, start, count, last_values):
        return self.lower().replace("_", "-")

    def __str__(self):
        # when processing json() for response creation,
        # automatically convert to the generated value
        return self.value


class ConsentAction(EnumNameHyphenCase):
    FIRST_NAME_READ = auto()
    FIRST_NAME_WRITE = auto()
    LAST_NAME_READ = auto()
    LAST_NAME_WRITE = auto()
    EMAIL_READ = auto()
    EMAIL_WRITE = auto()
    READ_DATA = auto()
    SHARE_DATA = auto()
    WRITE_DATA = auto()
    READ_FILE = auto()
    SHARE_FILE = auto()
    WRITE_FILE = auto()


class ConsentType(EnumNameHyphenCase):
    CREATED = auto()  # default consent created on first block or until change applied for given action
    CHANGED = auto()  # resolved consent action with existing and explicit definition of active consent
    EXPIRED = auto()  # when last consent was still granted, but is now passed specified expiration datetime
    UNDEFINED = auto()  # when no consent was define for the corresponding action (ie: created time always changes)


class DataType(EnumNameHyphenCase):
    TEXT = auto()
    AUDIO = auto()
    IMAGE = auto()
    VIDEO = auto()
    DOCUMENT = auto()
    MESSAGE = auto()
    OTHER = auto()
    UNDEFINED = auto()


class SingletonMeta(type):
    __instance__ = None  # type: Optional[SingletonMeta]

    def __call__(cls):
        if cls.__instance__ is None:
            cls.__instance__ = super(SingletonMeta, cls).__call__()
        return cls.__instance__


class Null(metaclass=SingletonMeta):
    """
    Represents a ``null`` value to differentiate from ``None``.
    """

    # pylint: disable=E1101,no-member
    def __eq__(self, other):
        # type: (Any) -> bool
        """
        Makes any instance of :class:`NullType` compare as the same (ie: Singleton).
        """
        return (isinstance(other, NullType)                                     # noqa: W503
                or other is null                                                # noqa: W503
                or other is self.__instance__                                   # noqa: W503
                or (inspect.isclass(other) and issubclass(other, NullType)))    # noqa: W503

    def __getattr__(self, item):
        # type: (Any) -> NullType
        """
        Makes any property getter return ``null`` to make any sub-item also look like ``null``.

        Useful for example in the case of type comparators that do not validate their
        own type before accessing a property that they expect to be there. Without this
        the get operation on ``null`` would raise an unknown key or attribute error.
        """
        return null

    def __repr__(self):
        return "<null>"

    @staticmethod
    def __nonzero__():
        return False

    __bool__ = __nonzero__
    __len__ = __nonzero__


null = Null()


class SubSystem(Base):
    def __init__(self,
                 data: Optional[Union[str, bytes, Null]] = null,
                 data_type: Optional[Union[str, DataType]] = None,
                 data_hash: Optional[str] = None,
                 data_description: Optional[str] = None,
                 data_source: Optional[str] = None,
                 data_provider: Optional[str] = None,
                 media_type: Optional[str] = None,
                 metadata: Optional[Union[Mapping, str]] = None,
                 **kwargs: Any,
                 ) -> None:
        super(SubSystem, self).__init__(**kwargs)
        # NOTE: use 'Base' for below operations to generate the undefined properties required by 'json()' method
        if data is null and data_hash:  # hash not in request body
            Base.__setattr__(self, "data_hash", data_hash)  # load from storage
        elif data:
            data_hash = compute_hash(data)
            Base.__setattr__(self, "data_hash", data_hash)
        elif data is None and data_hash is None:  # data=None mean explicit None (JSON null) in request
            Base.__setattr__(self, "data_hash", None)   # metadata only subsystem
        else:
            raise ValueError("Missing either literal data to hash or precomputed data hash.")
        Base.__setattr__(self, "data_type", data_type)
        if data and not media_type:
            media_type = magic.from_buffer(data, mime=True)
        Base.__setattr__(self, "media_type", media_type)  # attempt auto-resolve media-type from data type
        if self.data_type != data_type:
            if data_type is not None:
                self.data_type = data_type   # update if not resolved or different
            else:
                self.data_type = DataType.UNDEFINED
        Base.__setattr__(self, "data_source", data_source)
        Base.__setattr__(self, "data_provider", data_provider)
        Base.__setattr__(self, "data_description", data_description)
        Base.__setattr__(self, "metadata", metadata)

    def json(self, force=True) -> JSON:
        data = super(SubSystem, self).json(force=force)
        data.pop("data", None)  # make sure literal data never makes its way here (to ensure privacy)
        return data

    @property
    def data_type(self) -> DataType:
        return self["data_type"]

    @data_type.setter
    def data_type(self, data_type: Union[str, DataType]) -> None:
        try:
            data_type = DataType(data_type)
        except ValueError:
            if data_type:
                data_type = DataType.OTHER
            else:
                data_type = DataType.UNDEFINED
        self["data_type"] = data_type

    @property
    def data_description(self) -> Optional[str]:
        desc = self["data_description"]
        if not isinstance(desc, str):
            return None
        return desc

    @data_description.setter
    def data_description(self, data_description: Optional[str]):
        if isinstance(data_description, str) or data_description is None:
            self["data_description"] = data_description

    @property
    def media_type(self) -> Optional[str]:
        desc = self["media_type"]
        if not isinstance(desc, str):
            return None
        return desc

    @media_type.setter
    def media_type(self, media_type: Optional[str]):
        if media_type is None:
            self["media_type"] = None
            return
        if isinstance(media_type, str):
            media_type = media_type.lower()
            if "/" in media_type and media_type.split("/")[0] in KNOWN_MEDIA_TYPES:
                self["media_type"] = media_type
            else:
                self["media_type"] = "plain/text"
            media_type = self["media_type"]
        if not isinstance(self.data_type, DataType):
            if not media_type:
                self.data_type = DataType.UNDEFINED
            else:
                self.data_type = media_type.split("/")[0]

    @property
    def metadata(self) -> Optional[Union[Mapping, str]]:
        meta = self["metadata"]
        if meta is None:
            return None
        try:
            return json.loads(meta)
        except (JSONDecoder, TypeError, ValueError):
            return str(meta)

    @metadata.setter
    def metadata(self, meta: Optional[Union[Mapping, str]]):
        if isinstance(meta, str) or meta is None:
            self["metadata"] = meta
            return
        try:
            json.dumps(meta)
            self["metadata"] = meta
        except (TypeError, ValueError):
            self["metadata"] = str(meta)


class Consent(WithDatetime):
    def __init__(self,
                 action: Union[str, ConsentAction],
                 consent: bool,
                 *args: Any,
                 expire: Optional[Union[str, datetime]] = None,
                 consent_type: Union[str, ConsentType] = ConsentType.UNDEFINED,
                 subsystems: Optional[List[SubSystem]] = None,
                 **kwargs: Any,
                 ) -> None:
        dict.__setattr__(self, "action", action)
        self["consent"] = consent
        dict.__setattr__(self, "expire", expire)
        dict.__setattr__(self, "type", kwargs.pop("type", None) or consent_type)  # bw-compat & reload from JSON
        dict.__setattr__(self, "subsystems", subsystems or [])
        super(Consent, self).__init__(*args, **kwargs)

    def __repr__(self):
        expire = "forever" if self.expire is None else f"until [{self.expire}]"
        return f"{self.action!s} [consent:{int(self.consent)}] from [{self.created}] {expire}"

    @property
    def action(self) -> ConsentAction:
        return self["action"]

    @action.setter
    def action(self, action: Union[str, ConsentAction]) -> None:
        self["action"] = ConsentAction(action)

    @property
    def expire(self) -> Optional[datetime]:
        return dict.__getitem__(self, "expire")

    @expire.setter
    def expire(self, expire: Optional[Union[str, datetime]]) -> None:
        if expire is None:
            self["expire"] = None
            return
        if not isinstance(expire, (str, datetime)):
            raise TypeError(f"Invalid expire type: {type(expire)!s}")
        if isinstance(expire, str):
            expire = dt_parser.parse(expire)
        self["expire"] = expire

    @property
    def type(self) -> ConsentType:
        return self["type"]

    @type.setter
    def type(self, consent_type: Union[str, ConsentType]) -> None:
        self["type"] = ConsentType(consent_type)

    consent_type = type

    @property
    def subsystems(self) -> List[SubSystem]:
        return self["subsystems"]

    @subsystems.setter
    def subsystems(self, subsystems: List[Union[SubSystem, JSON]]):
        self["subsystems"] = [SubSystem(**dict(sub)) if not isinstance(sub, SubSystem) else sub for sub in subsystems]


class ConsentChange(WithDatetime):
    """
    Holds modified consents and generates complete consents history from them.
    """
    def __init__(self,
                 *args: Any,
                 consents: Optional[Iterable[Union[Consent, JSON]]] = None,
                 **kwargs: Any,
                 ) -> None:
        """
        Create a new consent change definition.

        Only the modified consents should be provided to reduce space in storage.
        Duplicate consents will be ignored when generating change history.
        """
        if not consents:
            consents = []
        else:
            consents = [Consent(**consent) if not isinstance(consent, Consent) else consent for consent in consents]
        self["consents"] = consents
        super(ConsentChange, self).__init__(*args, **kwargs)

    @property
    def consents(self) -> List[Consent]:
        """
        Obtain this block's consents (optionally changed) sorted by creation date.
        """
        return list(sorted(self["consents"], key=lambda c: c.created))

    @classmethod
    def latest(cls, chain: "Blockchain") -> List[Consent]:
        """
        Compute the latest consents resolution cumulated over the whole blockchain history.

        If any known action does not provide any corresponding consent, it is defaulted to not consented.
        """
        chain.setdefault("states", {})
        last_id = chain.states.consent_change_last_id
        if not last_id or chain.last_block.id != last_id:
            cls.history(chain)  # resolve it
        consents = chain.states.consent_change_updated
        undefined = [Consent(action, False) for action in ConsentAction if action not in consents]
        resolved = list(sorted(list(consents.values()) + undefined, key=lambda c: c.action.value))
        for consent in resolved:
            if consent.expire and datetime.utcnow() > consent.expire:
                consent.type = ConsentType.EXPIRED
                consent.consent = False
        return resolved

    @classmethod
    def history(cls, chain: "Blockchain") -> List[str]:
        """
        Compute the change history of consents across a blockchain.
        """

        # speed up skipping pre-computed without changes
        changes = chain.states.consent_change_history  # type: List[str]
        last_id = chain.states.consent_change_last_id  # type: Optional[uuid.UUID]
        updated = chain.states.consent_change_updated  # type: Dict[ConsentAction, Consent]
        updated = dict(updated)  # copy to allow setting frozen dict when resolving actions
        if changes and last_id and last_id == chain.last_block.id:
            LOGGER.debug("Using precomputed consent change history for blockchain [%s]", chain.id)
            return changes

        LOGGER.debug("Computing consent change history for blockchain [%s]", chain.id)
        prev_block = None  # type: Optional[Block]
        remain_blocks = chain.blocks
        if last_id:
            # previously pre-processed but didn't apply latest changes
            # skip until missing block updates
            for i in range(len(remain_blocks)):
                if remain_blocks[i].id == last_id:
                    prev_block = remain_blocks[i]
                    remain_blocks = remain_blocks[i + 1:]
                    break

        for block in remain_blocks:
            # first block always creates initial consents
            if prev_block is None:
                for consent in block.consents:
                    changes.append(f"[created] => {consent!r}")
                    consent.type = ConsentType.CREATED
                    updated[consent.action] = consent
                if not changes:
                    changes.append("[initial] => (no consents)")
            # check following block for change of consents
            else:
                for consent in block.consents:
                    prev_consent = updated.get(consent.action)
                    consent.type = ConsentType.CHANGED
                    if prev_consent is None or prev_consent != consent:
                        updated[consent.action] = consent
                        changes.append(f"[updated] => {consent!r}")
                    else:
                        changes.append(f"[updated] =>> block without consents change")
            prev_block = block

        chain.states.unfreeze()
        chain.states.consent_change_history = changes
        chain.states.consent_change_updated = updated
        chain.states.consent_change_last_id = prev_block.id if prev_block else None
        chain.states.freeze()
        return changes


class Node(Base):
    def __init__(self, url, id=None):
        self._id = id
        self._fix_url(url)
        super(Node, self).__init__()
        if self._id is None:
            self.sync_id()

    def __getitem__(self, item):
        if item == "id":
            return self._id
        return super(Node, self).__getitem__(item)

    @property
    def _id(self):
        return dict.__getitem__(self, "_id")

    @_id.setter
    def _id(self, _id: Optional[AnyUUID]):
        if isinstance(_id, str):
            _id = UUID(_id)
        if _id is not None and not isinstance(_id, UUID):
            raise TypeError(f"Invalid UUID: {_id!s}")
        dict.__setattr__(self, "_id", _id)

    @property
    def id(self):
        if not self["id"]:
            self.sync_id()
        return self["id"]

    @property
    def url(self):
        return self["url"]

    @property
    def resolved(self):
        return self.id is not None  # attempts inline resolve

    def json(self, **__):
        _id = self.id  # inline resolve as needed if it becomes available
        return {"id": _id, "url": self.url, "resolved": _id is not None}

    def _fix_url(self, endpoint):
        parsed_url = urlparse(endpoint)
        if parsed_url.netloc:
            url = parsed_url.netloc
        elif parsed_url.path:
            # Accepts an URL without scheme like "192.168.0.5:5000".
            url = parsed_url.path
        else:
            raise ValueError(f"Invalid node location: [{endpoint}]")
        if not url.startswith("http"):
            url = f"http://{url}"
        self["url"] = url

    def sync_id(self):
        self._id = None  # reset (from Base)
        try:
            resp = requests.get(self.url, timeout=2)
            if resp.status_code == 200:
                self._id = resp.json()["node"]
                return
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass
        LOGGER.warning("Node ID not yet resolved for location: [%s]", self.url)


class Block(ConsentChange):
    """
    Block used to form the chain.
    """

    def __init__(self, *args, **kwargs):
        self.update({
            "index": None,
            "proof": None,
            "previous_hash": None,
            "transactions": [],
        })
        if args:
            if len(args) == 1 and isinstance(args[0], dict):
                items = dict(**args[0])
                kwargs.update(items)
            else:
                items = dict(*args)
                kwargs.update(items)
        super(Block, self).__init__(**kwargs)

    @property
    def hash(self):
        # type: () -> str
        """
        Generate the hash representation of the contents of this block.
        """
        # ensure that the Dictionary is Ordered, or hashes will become inconsistent
        # hash must combine JSON representation such that other nodes can compute it as well
        block_str = json.dumps(self.json(), sort_keys=True).encode()
        block_hash = compute_hash(block_str)
        return block_hash


class Blockchain(Base):
    def __init__(self,
                 chain: Optional[Iterable[Block]] = None,
                 genesis_block: bool = True,
                 difficulty: int = 4,
                 *_: Any,
                 **__: Any,
                 ) -> None:
        """
        Initialize the blockchain.

        :param chain:
            Predefined list of blocks to load.
            If blocks are provided, they are loaded as is.
            Otherwise, generate the genesis block.
        :param genesis_block:
            Genesis block generation can be skipped if running initial resolution against other nodes.
        :param difficulty:
            Hashing validation difficulty as the amount of successive zeros needed guess the next block as valid.
        """
        super(Blockchain, self).__init__(*_, **__)
        self.difficulty = difficulty
        self.pending_transactions = []
        self.pending_consents = []
        LOGGER.warning("CHAIN: %s", chain)
        self["blocks"] = [
            block if isinstance(block, Block) else Block(**block)
            for block in chain or []
        ]
        self.setdefault("updated", datetime.utcnow())
        self.setdefault("states", AttributeDict({
            "consent_change_history": [],       # type: List[str]
            "consent_change_updated": {},       # type: Dict[ConsentAction, Consent]
            "consent_change_last_id": None,     # type: Optional[uuid.UUID]
        }))
        self.states.freeze()  # only history computation can modify with explicit unfreeze

        # Create the genesis block
        if not self.blocks and genesis_block:
            self.new_block(previous_hash="1", proof=100)

    def __getitem__(self, item):
        if isinstance(item, int):
            # shortcut to fetch blocks by index directly
            return self.blocks[item]
        return super(Blockchain, self).__getitem__(item)

    def __len__(self):
        return len(self.blocks)

    def _set_updated(self):
        self["updated"] = datetime.utcnow()

    @property
    def updated(self):
        return self["updated"]

    def json(self, *_: Any, detail: bool = False, **__: Any) -> JSON:
        return {
            "id": str(self.id),
            "updated": self.updated.isoformat(),
            "blocks": [block.json() if detail else str(block.id) for block in self.blocks]
        }

    def data(self,
             *_: Any,
             detail: bool = False,
             **__: Any,
             ) -> Dict[str, Union[uuid.UUID, datetime, Union[Block, uuid.UUID]]]:
        return {
            "id": self.id,
            "updated": self.updated,
            "blocks": self.blocks if detail else [block.id for block in self.blocks]
        }

    @property
    def blocks(self) -> List[Block]:
        return self["blocks"]

    @blocks.setter
    def blocks(self, chain):
        self["blocks"] = [Block(block) for block in chain]
        self._set_updated()

    chain = blocks  # alias

    def valid_chain(self, chain: "Blockchain") -> bool:
        """
        Determine if a given blockchain is valid.

        :param chain: A blockchain
        :returns: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        LOGGER.debug("--- (validate) ---")
        while current_index < len(chain):
            block = chain[current_index]
            LOGGER.debug("Previous: %s", last_block)
            LOGGER.debug("Current:  %s", block)
            LOGGER.debug("------------------")
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block["previous_hash"] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block["proof"], block["proof"], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self, nodes: Iterable[Node]) -> Tuple[bool, List[Node]]:
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :returns:
            Tuple of:
                - True if our chain was replaced, False if not
                - List of all nodes that were available and consensus validation could be processed against
        """

        new_chain = None
        validated = []

        # We're only looking for chains longer than ours
        max_length = len(self.blocks)

        # Grab and verify the chains from all the nodes in our network
        for node in nodes:
            try:
                response = requests.get(f"{node.url}/chains/{self.id!s}/blocks?detail=true", timeout=2)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                LOGGER.warning("Node [%s] is unresponsive for conflict resolution. Skipping it.", node.url)
                continue

            if response.status_code != 200:
                LOGGER.warning("Node [%s] responded with invalid code [%s] during conflict resolution. "
                               "Skipping it.", node, response.status_code)
                continue

            validated.append(node)
            body = response.json()
            length = body["length"]
            chain = Blockchain(chain=body["blocks"], id=self.id)

            # Check if the length is longer and the chain is valid
            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.blocks = new_chain.blocks
            return True, validated

        return False, validated

    def verify_outdated(self, nodes: Iterable[Node]) -> Optional[bool]:
        """
        Verifies if a given blockchain is considered outdated (potentially unresolved) against other nodes.

        Contrary to the consensus resolution, only verifies the latest block assuming that historical hashes
        are correctly embedded in previous blocks and last one should match, instead of validating each one.
        This is for quick verification whether a full consensus resolution should even be considered or not.

        :returns:
            - ``None`` if all remote nodes are unresponsive or the blockchain cannot be found on any node.
            - ``True`` if the blockchain is of same length and hash as other remote nodes.
            - ``False`` otherwise
        """
        outdated = None
        for node in nodes:
            try:
                resp = requests.get(f"{node.url}/chains/{self.id}/blocks?detail=true", timeout=2)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                LOGGER.warning("Node [%s] is unresponsive for outdated verification. Skipping it.", node.url)
                continue
            if resp.status_code == 200:
                body = resp.json()
                length = len(self)
                # current chain could be the most updated with other nodes being outdated
                # therefore allow greater length for this node, but still validate hash
                if length >= body["length"]:
                    offset = length - body["length"]
                    index = length - offset - 1
                    block = self.blocks[index]
                    other = Block(body["blocks"][index])
                    if block.hash == other.hash:
                        outdated = False  # for now valid, but continue until last node
                # stop on any more recent node that can be validated
                else:
                    index = length - 1
                    block = self.blocks[index]
                    other = Block(body["blocks"][index])
                    if block.hash == other.hash:
                        return True
                    # otherwise, unknown conflict - cannot ensure if outdated or not
        return outdated

    def new_block(self, proof: int, previous_hash: Optional[str] = None) -> Block:
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block, or compute it from last block in chain.
        :returns: New Block
        """
        block = Block({
            "index": len(self.blocks),
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.blocks[-1]),
            "transactions": self.pending_transactions,
            "consents": self.pending_consents,
        })

        # Reset the current list of transactions
        self.pending_transactions = []
        self.pending_consents = []

        self.blocks.append(block)
        return block

    def new_transaction(self, sender: str, recipient: str, amount: Union[int, float, Decimal]) -> int:
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :returns: The index of the Block that will hold this transaction
        """
        self.pending_transactions.append(Transaction({
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
        }))

        return self.last_block["index"] + 1

    def new_consent(self,
                    action: ConsentAction,
                    consent: bool,
                    expire: datetime,
                    subsystems: Optional[List[SubSystem]] = None,
                    ) -> int:
        """
        Creates a new consents to go into the next mined block.

        :param action: consent action to be modified
        :param consent: consent status (granted/revoked) regarding the action
        :param expire: expiration date and time of the consent (none if forever until modified)
        :param subsystems: metadata about the data onto which consents are applied
        :returns: index of the block that will hold this new consent change
        """
        self.pending_consents.append(Consent(
            action=action,
            expire=expire,
            consent=consent,
            consent_type=ConsentType.CHANGED,
            subsystems=subsystems,
        ))
        return self.last_block["index"] + 1

    @property
    def last_block(self) -> Block:
        return self.blocks[-1]

    @staticmethod
    def hash(block: Block) -> str:
        """
        Creates a SHA-256 hash of a :class:`Block`.
        """
        return block.hash

    def proof_of_work(self, last_block: Block) -> int:
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param last_block: last Block
        :returns: computed proof
        """

        last_proof = last_block["proof"]
        last_hash = self.hash(last_block)

        proof = 0
        while not self.valid_proof(last_proof, proof, last_hash):
            proof += 1

        return proof

    def valid_proof(self, last_proof: int, proof: int, last_hash: str) -> bool:
        """
        Validates the Proof

        :param last_proof: Previous Proof
        :param proof: Current Proof
        :param last_hash: The hash of the Previous Block
        :returns: True if correct, False if not.
        """

        guess = f"{last_proof}{proof}{last_hash}"
        guess_hash = compute_hash(guess)
        guess_valid = "0" * self.difficulty
        return guess_hash[:self.difficulty] == guess_valid


class MultiChain(dict):
    """
    Mapping of UUID to Blockchain with types validation and conversion.
    """
    def __setattr__(self, key, value):
        self[key] = value

    def __setitem__(self, key, value):
        if not isinstance(value, Blockchain):
            raise ValueError(f"Not a blockchain: {value}")
        if not isinstance(key, uuid.UUID):
            key = uuid.UUID(key)
        dict.__setitem__(self, key, value)
