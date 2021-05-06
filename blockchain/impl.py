import abc
import datetime
import hashlib
import json
import uuid
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import requests
from addict import Dict as AttributeDict  # auto generates attribute, properties and getter/setter dynamically

from blockchain.utils import get_logger

if TYPE_CHECKING:
    from typing import Any, Dict, List, Optional
    from blockchain import JSON

LOGGER = get_logger(__name__)


class Base(AttributeDict, abc.ABC):
    """
    Dictionary with extended attributes auto-``getter``/``setter`` for convenience.
    Explicitly overridden ``getter``/``setter`` attributes are called instead of ``dict``-key ``get``/``set``-item
    to ensure corresponding checks and/or value adjustments are executed before applying it to the sub-``dict``.
    """

    __json__ = True  # repr as JSON

    def __init__(self, *args, **kwargs):
        super(Base, self).__init__(*args, **kwargs)
        self.setdefault("id", uuid.uuid4())

    def __str__(self):
        # type: () -> str
        return "{0} <{1}>".format(type(self).__name__, self.id)

    # FIXME: remove when integrated (https://github.com/mewwts/addict/pull/139)
    def __repr__(self):
        if self.__json__:
            cls = type(self)
            try:
                repr_ = json.dumps(self.json(force=False), indent=2, ensure_ascii=False)
            except Exception:  # noqa
                return dict.__repr__(self)
            return "{0}.{1}\n{2}".format(cls.__module__, cls.__name__, repr_)
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


class Block(Base):
    """
    Block used to form the chain.
    """

    def __init__(self, *args, **kwargs):
        self.update({"index": None, "transactions": [], "proof": None, "previous_has": None})
        super(Block, self).__init__(*args, **kwargs)
        self.setdefault("timestamp", self.timestamp)  # generate

    @property
    def timestamp(self):
        # type: () -> str
        dt = self.get("timestamp")
        if dt is None:
            dt = datetime.datetime.utcnow().isoformat()
            self["timestamp"] = dt
        return dt


class Transaction(Base):
    pass


class Blockchain(Base):
    def __init__(self, chain=None, *_, **__):

        super(Blockchain, self).__init__(*_, **__)
        self.current_transactions = []
        self["blocks"] = chain or []
        self.nodes = set()

        # Create the genesis block
        if not self.blocks:
            self.new_block(previous_hash="1", proof=100)

    def json(self, *_, **__):
        # type: (Any, Any) -> JSON
        return {
            "id": self.id,
            "chain": [block.id for block in self.blocks],
            "nodes": list(self.nodes)
        }

    @property
    def blocks(self):
        # type: () -> List[Block]
        return self["blocks"]

    @blocks.setter
    def blocks(self, chain):
        self["blocks"] = [Block(block) for block in chain]

    chain = blocks  # alias

    def register_node(self, address):
        """
        Add a new node to the list of nodes

        :param address: Address of node. Eg. "http://192.168.0.5:5000"
        """

        parsed_url = urlparse(address)
        if parsed_url.netloc:
            self.nodes.add(parsed_url.netloc)
        elif parsed_url.path:
            # Accepts an URL without scheme like "192.168.0.5:5000".
            self.nodes.add(parsed_url.path)
        else:
            raise ValueError("Invalid URL")

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

    def resolve_conflicts(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: True if our chain was replaced, False if not
        """

        neighbours = self.nodes
        new_chain = None

        # We're only looking for chains longer than ours
        max_length = len(self.blocks)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get(f"http://{node}/chain")

            if response.status_code == 200:
                length = response.json()["length"]
                chain = response.json()["chain"]

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.blocks = new_chain
            return True

        return False

    def new_block(self, proof, previous_hash=None):
        # type: (int, Optional[str]) -> Block
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = Block({
            "index": len(self.blocks) + 1,
            "transactions": self.current_transactions,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.blocks[-1]),
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

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
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
