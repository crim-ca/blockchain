import abc
import json
import os
import uuid
from typing import TYPE_CHECKING

from blockchain.impl import Block, Blockchain, MultiChain
from blockchain.utils import get_logger, is_uuid

if TYPE_CHECKING:
    from typing import Optional, Tuple, Union

    AnyUUID = Union[str, uuid.UUID]

LOGGER = get_logger(__name__)


class Database(abc.ABC):
    @abc.abstractmethod
    def load_multi_chain(self):
        # type: () -> MultiChain
        raise NotImplementedError

    @abc.abstractmethod
    def save_multi_chain(self, multi_chain):
        # type: (MultiChain) -> None
        raise NotImplementedError

    @abc.abstractmethod
    def load_chain(self, chain_id=None):
        # type: (Optional[AnyUUID]) -> Blockchain
        raise NotImplementedError

    @abc.abstractmethod
    def save_chain(self, chain):
        # type: (Blockchain) -> None
        raise NotImplementedError

    @abc.abstractmethod
    def load_block(self, block_id, chain_id=None):
        # type: (AnyUUID, Optional[AnyUUID]) -> Block
        raise NotImplementedError

    @abc.abstractmethod
    def save_block(self, block, chain_id=None):
        # type: (Block, Optional[AnyUUID]) -> None
        raise NotImplementedError


class FileSystemDatabase(Database):
    def __init__(self, path, *args, **kwargs):
        super(FileSystemDatabase, self).__init__(*args, **kwargs)
        self.dir = ""
        self.txt = ""
        self.path = ""
        self.multi = False
        path = path.split("://")[-1]
        if os.path.isfile(path) and path.endswith(".json"):
            self.path = path
        elif os.path.isfile(path) and path.endswith(".txt"):
            self.dir = os.path.dirname(path)
            self.txt = path
        elif os.path.isdir(path):
            self.dir = path
            chain = os.path.join(path, "chain.json")
            if os.path.isfile(chain) and chain.endswith(".json"):
                self.path = chain

    @property
    def stored(self):
        return os.path.isfile(self.path)

    def get_chain_location(self, chain_id):
        # type: (Optional[AnyUUID]) -> Tuple[str, str]
        if self.stored and not self.multi:
            store_path = os.path.dirname(self.path)
            chain_path = self.path
        else:
            path = (os.path.dirname(self.path) if self.multi else self.path) or self.dir
            if chain_id:
                store_path = os.path.join(path, str(chain_id))
            else:
                store_path = path
            chain_path = os.path.join(store_path, "chain.json")
        return store_path, chain_path

    def load_multi_chain(self):
        # type: () -> MultiChain
        """
        Loads multiple blockchains from file system.
        """
        store_path, chain_path = self.get_chain_location(None)
        if self.txt:
            with open(self.txt, "r") as txt:
                data = {"chains": txt.readlines()}
        elif self.dir:
            data = {"chains": [
                chain_dir for chain_dir in os.listdir(store_path)
                if (is_uuid(chain_dir) and
                    os.path.isdir(os.path.join(self.dir, chain_dir)) and
                    os.path.isfile(os.path.join(self.dir, chain_dir, "chain.json")))
            ]}
        elif not os.path.isfile(chain_path):
            LOGGER.warning("No such chain: [%s]", chain_path)
            return MultiChain()
        else:
            with open(chain_path) as chain_file:
                data = json.load(chain_file)
        chains = MultiChain()
        if "chains" in data:
            self.multi = True
            for chain in data["chains"]:
                blockchain = self.load_chain(chain)
                chains[blockchain.id] = blockchain
        elif "chain" in data:
            # actually only a single chain, but load as multi for backward compat
            blockchain = self.load_chain(data["chain"])  # noqa
            chains[blockchain.id] = blockchain
        else:
            raise ValueError("Invalid blockchain(s) format, missing chain(s) field.")
        return chains

    def load_chain(self, chain_id=None):
        # type: (Optional[AnyUUID]) -> Blockchain
        """
        Load blockchain from file system.
        """
        LOGGER.debug("Loading chain: [%s]", chain_id)
        blocks = []
        store_path, chain_path = self.get_chain_location(chain_id)
        if not os.path.isfile(chain_path):
            LOGGER.warning("No such chain: [%s]", chain_path)
        else:
            with open(chain_path) as chain_file:
                blockchain = json.load(chain_file)
            chain_id = uuid.UUID(blockchain["id"])
            LOGGER.info("%s blocks in chain [%s]", len(blockchain["blocks"]), chain_path)
            for block_id in blockchain["blocks"]:
                block = self.load_block(block_id, chain_id)
                blocks.append(block)
        return Blockchain(chain=blocks, id=chain_id)

    def load_block(self, block_id, chain_id=None):
        # type: (AnyUUID, Optional[AnyUUID]) -> Block
        """
        Load a single block from file system.
        """
        store_path, _ = self.get_chain_location(chain_id)
        block_path = os.path.join(store_path, f"{block_id!s}.json")
        with open(block_path) as block_file:
            block = json.load(block_file)
        return Block(**block)

    def save_multi_chain(self, multi_chain):
        # type: (MultiChain) -> None
        """
        Saves multiple blockchain to file system.
        """
        # only need to update the references since each chain is individually
        # saved whenever updated by the API new block/consensus resolution
        store_path, _ = self.get_chain_location(None)
        os.makedirs(store_path, exist_ok=True)
        multi_path = os.path.join(store_path, "chains.txt")
        with open(multi_path, "w") as txt:
            txt.writelines([str(chain.id) for chain in multi_chain])

    def save_chain(self, chain):
        # type: (Blockchain) -> None
        """
        Save blockchain to file system.
        """
        store_path, chain_path = self.get_chain_location(chain.id)
        os.makedirs(store_path, exist_ok=True)
        with open(chain_path, "w") as chain_file:
            json.dump(chain.json(), chain_file)
        for block in chain.blocks:
            self.save_block(block, chain_id=chain.id)
        if not self.stored:
            self.path = chain_path

    def save_block(self, block, chain_id=None):
        # type: (Block, Optional[AnyUUID]) -> None
        """
        Save a single block from the chain to file system.
        """
        store_path, _ = self.get_chain_location(chain_id)
        block_path = os.path.join(store_path, f"{block.id!s}.json")
        if os.path.isfile(block_path):
            return
        with open(block_path, "w") as block_file:
            json.dump(block.json(), block_file)


# known implementations
DB_TYPES = {
    "file": FileSystemDatabase
}
