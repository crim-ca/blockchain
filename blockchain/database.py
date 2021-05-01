import abc
import json
import os
from typing import TYPE_CHECKING

from blockchain.impl import Block, Blockchain
from blockchain.utils import get_logger

if TYPE_CHECKING:
    from typing import Optional

LOGGER = get_logger(__name__)


class Database(abc.ABC):
    def __init__(self, *args, **kwargs):
        self.chain = []

    @abc.abstractmethod
    def load_chain(self, chain_id=None):
        # type: (Optional[str]) -> Blockchain
        raise NotImplementedError

    @abc.abstractmethod
    def save_chain(self, chain):
        # type: (Blockchain) -> None
        raise NotImplementedError

    @abc.abstractmethod
    def load_block(self, block_id, chain_id=None):
        # type: (str, Optional[str]) -> Block
        raise NotImplementedError

    @abc.abstractmethod
    def save_block(self, block, chain_id=None):
        # type: (Block, Optional[str]) -> None
        raise NotImplementedError


class FileSystemDatabase(Database):
    def __init__(self, path, *args, **kwargs):
        super(FileSystemDatabase, self).__init__(*args, **kwargs)
        self.path = path.split("://")[-1]
        os.makedirs(self.path, exist_ok=True)

    def get_chain_location(self, chain_id):
        if chain_id:
            store_path = os.path.join(self.path, chain_id)
        else:
            store_path = os.path.join(self.path)
        chain_path = os.path.join(store_path, "chain.json")
        return store_path, chain_path

    def load_chain(self, chain_id=None):
        # type:
        """
        Load blockchain from file system.
        """
        chain = []
        store_path, chain_path = self.get_chain_location(chain_id)
        if not os.path.isfile(chain_path):
            LOGGER.warning("No such chain: [%s]", chain_path)
        else:
            with open(chain_path) as chain_file:
                block_ids = json.load(chain_file)
            LOGGER.info("%s blocks in chain [%s]", len(block_ids), chain_path)
            for block_id in block_ids:
                block = self.load_block(block_id, chain_id)
                chain.append(block)
        return Blockchain(chain, id=chain_id)

    def load_block(self, block_id, chain_id=None):
        # type: (str, Optional[str]) -> Block
        """
        Load a single block from file system.
        """
        store_path, _ = self.get_chain_location(chain_id)
        block_path = os.path.join(store_path, "{}.json".format(block_id))
        with open(block_path) as block_file:
            block = json.load(block_file)
        return Block(block)

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

    def save_block(self, block, chain_id=None):
        # type: (Block, Optional[str]) -> None
        """
        Save a single block from the chain to file system.
        """
        store_path, _ = self.get_chain_location(chain_id)
        block_path = os.path.join(store_path, "{}.json".format(block.id))
        with open(block_path, "w") as block_file:
            json.dump(block.json(), block_file)


# known implementations
DB_TYPES = {
    "file": FileSystemDatabase
}
