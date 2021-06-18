import abc
import datetime
import hashlib
import json
import uuid
from enum import Enum, auto
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import requests
from dateutil import parser as dt_parser
from addict import Dict as AttributeDict  # auto generates attribute, properties and getter/setter dynamically

from blockchain.utils import get_logger

if TYPE_CHECKING:
    from typing import Any, Dict, Iterable, List, Optional, Tuple
    from blockchain import JSON

LOGGER = get_logger(__name__)


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
    def json(self, force=True):
        # type: (bool) -> JSON
        """
        JSON representation of the data.
        """
        base = {}
        _typ = type(self)
        for key, value in self.items():
            key = str(key)  # ensure conversion
            if isinstance(value, (_typ, dict)):
                base[key] = _typ(value).json()
            elif isinstance(value, (list, tuple)):
                base[key] = list(
                    (_typ(item).json() if callable(item.json) else _typ(item).json)
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

    def params(self):
        # type: () -> Dict[str, Any]
        """
        Obtain the internal data representation for storage.
        """
        return dict(self)


class WithDatetime(Base):
    def __init__(self, *args, **kwargs):
        # generate or set created datetime
        created = kwargs.pop("created", kwargs.pop("timestamp", self.created))
        self.setdefault("created", created)
        super(WithDatetime, self).__init__(*args, **kwargs)

    @property
    def created(self):
        # type: () -> str
        dt = self.get("created")
        if dt is None:
            dt = datetime.datetime.utcnow().isoformat()
            self["created"] = dt
        return dt


class Transaction(Base):
    pass


class EnumNameHyphenCase(Enum):
    def _generate_next_value_(self, start, count, last_values):
        return self.lower().replace("_", "-")


class ConsentAction(EnumNameHyphenCase):
    FIRST_NAME_READ = auto()
    FIRST_NAME_WRITE = auto()
    LAST_NAME_READ = auto()
    LAST_NAME_WRITE = auto()
    EMAIL_READ = auto()
    EMAIL_WRITE = auto()

    def __str__(self):
        return self.value


class Consent(WithDatetime):
    def __init__(self, action, consent, *args, expire=None, **kwargs):
        # type: (ConsentAction, bool, Any, Any) -> None
        self["action"] = action
        self["consent"] = consent
        self["expire"] = expire
        super(Consent, self).__init__(*args, **kwargs)

    def __repr__(self):
        expire = "forever" if self.expire is None else f"until [{self.expire}]"
        return f"{self.action!s} [{int(self.consent)}] from [{self.created}] {expire}"

    @property
    def action(self):
        # type: () -> str
        return self["action"]

    @property
    def expire(self):
        dt = self["expire"]
        return datetime.datetime.fromisoformat(dt)

    @expire.setter
    def expire(self, expire):
        if not isinstance(expire, (str, datetime.datetime)):
            raise TypeError(f"Invalid expire type: {type(expire)!s}")
        if isinstance(expire, str):
            expire = dt_parser.parse(expire)
        self["expire"] = expire.isoformat()


class ConsentChange(WithDatetime):
    def __init__(self, *args, consents=None, **kwargs):
        # type: (Any, Optional[Iterable[Consent]], Any) -> None
        """
        Create a new consent change definition.

        Only the modified consents should be provided to reduce space in storage.
        Duplicate consents will be ignored when generating change history.
        """
        if not consents or not all(isinstance(consent, Consent) for consent in consents):
            consents = []
        self["consents"] = consents
        super(ConsentChange, self).__init__(*args, **kwargs)

    @property
    def consents(self):
        # type: () -> List[Consent]
        """
        Obtain this block's consents (optionally changed) sorted by creation date.
        """
        return list(sorted(self["consents"], key=lambda c: c.created))

    @classmethod
    def latest(cls, chain):
        # type: (Blockchain) -> List[Consent]
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
        return list(sorted(list(consents.values()) + undefined, key=lambda c: c.created))

    @classmethod
    def history(cls, chain):
        # type: (Blockchain) -> List[str]
        """
        Compute the change history of consents across a blockchain.
        """

        # speed up skipping pre-computed without changes
        changes = chain.states.consent_change_history  # type: List[str]
        updated = chain.states.consent_change_updated  # type: Dict[ConsentAction, Consent]
        last_id = chain.states.consent_change_last_id  # type: Optional[uuid.UUID]
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

        for block in remain_blocks:
            # first block always creates initial consents
            if prev_block is None:
                for consent in block.consents:
                    changes.append(f"[created] => {consent!r}")
                    updated[consent.action] = consent
                if not changes:
                    changes.append("[initial] => (no consents)")
            # check following block for change of consents
            else:
                for consent in block.consents:
                    prev_consent = updated.get(consent.action)
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
    def __init__(self, url):
        self._id = None
        self._fix_url(url)
        super(Node, self).__init__()
        self.sync_id()

    def __getitem__(self, item):
        if item == "id":
            return self._id
        return super(Node, self).__getitem__(item)

    @property
    def id(self):
        if not self["id"]:
            self._find_id()
        return self["id"]

    @property
    def url(self):
        return self["url"]

    def json(self, **__):
        _id = self.id  # inplace resolve as needed if it becomes available
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
        super(Block, self).__init__(*args, **kwargs)

    def hash(self):
        """
        Generate the hash representation of the contents of this block.
        """
        # ensure that the Dictionary is Ordered, or hashes will become inconsistent
        block_hash = json.dumps(self.json(), sort_keys=True).encode()
        return block_hash


class Blockchain(Base):
    def __init__(self, chain=None, *_, **__):
        # type: (Optional[Iterable[Block]], Any, Any) -> None
        """
        Initialize the blockchain.

        If blocks are provided, they are loaded as is.
        Otherwise, generate the genesis block.
        """
        super(Blockchain, self).__init__(*_, **__)
        self.current_transactions = []
        self["blocks"] = chain or []
        self.setdefault("updated", datetime.datetime.utcnow())
        self.setdefault("states", AttributeDict({
            "consent_change_history": [],       # type: List[str]
            "consent_change_updated": {},       # type: Dict[ConsentAction, Consent]
            "consent_change_last_id": None,     # type: Optional[uuid.UUID]
        }))
        self.states.freeze()  # only history computation can modify with explicit unfreeze

        # Create the genesis block
        if not self.blocks:
            self.new_block(previous_hash="1", proof=100)

    def _update(self):
        self["updated"] = datetime.datetime.utcnow()

    @property
    def updated(self):
        return self["updated"]

    def json(self, *_, detail=False, **__):
        # type: (Any, Any) -> JSON
        return {
            "id": str(self.id),
            "updated": self.updated.isoformat(),
            "blocks": [block.json() if detail else str(block.id) for block in self.blocks]
        }

    @property
    def blocks(self):
        # type: () -> List[Block]
        return self["blocks"]

    @blocks.setter
    def blocks(self, chain):
        self["blocks"] = [Block(block) for block in chain]
        self._update()

    chain = blocks  # alias

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: True if valid, False if not
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            LOGGER.debug("Last block:%s", last_block)
            LOGGER.debug("Current block:%s", block)
            LOGGER.debug("-----------")
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

    def resolve_conflicts(self, nodes):
        # type: (Iterable[Node]) -> Tuple[bool, bool]
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :returns:
            Tuple of:
                - True if our chain was replaced, False if not
                - True if other nodes were available for consensus validation or False
        """

        new_chain = None
        validated = False

        # We're only looking for chains longer than ours
        max_length = len(self.blocks)

        # Grab and verify the chains from all the nodes in our network
        for node in nodes:
            try:
                response = requests.get(f"{node.url}/chains/{self.id!s}/blocks", timeout=2)
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                LOGGER.warning("Node [%s] is unresponsive. Skipping it.", node.url)
                continue
            validated = True

            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["blocks"]

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.blocks = new_chain
            return True, validated

        return False, validated

    def new_block(self, proof, previous_hash=None):
        # type: (int, Optional[str]) -> Block
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = Block({
            "index": len(self.blocks),
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.blocks[-1]),
            "transactions": self.current_transactions,
        })

        # Reset the current list of transactions
        self.current_transactions = []

        self.blocks.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        # type: (str, str, int) -> int
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :param recipient: Address of the Recipient
        :param amount: Amount
        :return: The index of the Block that will hold this transaction
        """
        self.current_transactions.append(Transaction({
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
        }))

        return self.last_block["index"] + 1

    @property
    def last_block(self):
        # type: () -> Block
        return self.blocks[-1]

    @staticmethod
    def hash(block):
        # type: (Block) -> str
        """
        Creates a SHA-256 hash of a :class:`Block`.
        """
        block_string = block.hash()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block):
        # type: (Block) -> int
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof

        :param last_block: last Block
        :return: computed proof
        """

        last_proof = last_block["proof"]
        last_hash = self.hash(last_block)

        proof = 0
        while not self.valid_proof(last_proof, proof, last_hash):
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof, last_hash):
        # type: (int, int, str) -> bool
        """
        Validates the Proof

        :param last_proof: Previous Proof
        :param proof: Current Proof
        :param last_hash: The hash of the Previous Block
        :return: True if correct, False if not.
        """

        guess = f"{last_proof}{proof}{last_hash}".encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"


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
