import os.path

import argparse
import uuid
import logging
import sys
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic.errors import PydanticTypeError
from pydantic.validators import bool_validator, int_validator, float_validator
from uvicorn import Config, Server

from blockchain import AnyUUID, __meta__, __title__
from blockchain.api import BLOCK, CHAIN, MAIN, MAKO, NODES, VIEWS, schemas
from blockchain.database import DB_TYPES, Database
from blockchain.impl import Blockchain, MultiChain, Node
from blockchain.utils import get_logger, set_logger_config

LOGGER = get_logger("blockchain")


class BlockchainWebApp(FastAPI):
    blockchains: MultiChain = None
    nodes: List[Node] = None  # list instead of set to preserve order
    node: Node = None
    db: Database = None
    secret: str = None


# Instantiate the blockchain node webapp
APP = BlockchainWebApp(
    title=__title__,
    description=__meta__["Summary"],
    version=__meta__["Version"],
    contact={
        "name": __meta__["Maintainer"],
        "email": __meta__["Maintainer-email"],
        "responsibleOrganization": __meta__["Author"],
        "responsibleDeveloper": __meta__["Maintainer"],
        "url": __meta__["Home-page"],
    },
    license_info={
        "name": __meta__["License"],
    },
    docs_url="/api",
    openapi_url="/json",
)
APP.include_router(BLOCK)
APP.include_router(CHAIN)
APP.include_router(MAIN)
APP.include_router(NODES)
APP.include_router(VIEWS)
# serve static files via APP instead of VIEWS, router does not seem to work
APP.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "ui/static")))
APP.__name__ = __title__
MAKO.init_app(APP, pkg_path=os.path.dirname(__file__))


class DatabaseTypeAction(argparse.Action):
    choices = list(DB_TYPES)

    @classmethod
    def get_db(cls, value):
        if not isinstance(value, str):
            raise TypeError("Invalid database URI string")
        uri = urlparse(value)
        if uri.netloc:
            db_type = uri.scheme
            db_conn = uri.netloc
        else:
            if not uri.path.startswith("/"):
                raise ValueError(f"Database URI without scheme must be an absolute path: [{uri!s}]")
            db_type = "file"
            db_conn = uri.path
        db_impl = DB_TYPES.get(db_type)
        if not db_impl:
            raise ValueError(f"Unknown database type: [{db_type!s}]")
        return db_impl(db_conn)

    def __call__(self, parser, namespace, values, option_string=None):
        db = self.get_db(values)
        setattr(namespace, self.dest, db)


def parse_xargs(args: List[str], logger: logging.Logger) -> Dict[str, Union[str, int, float, bool]]:
    """
    Attempt to generate extra arguments directly for :mod:`uvicorn` configuration.
    """
    xargs = {}
    if args:
        if len(args) % 2 != 0:
            logger.error("Cannot parse odd number of extra arguments: %s", list(args))
            sys.exit(1)
        for i in range(0, len(args), 2):
            argn = args[i]
            argv = args[i + 1]
            if not argn.startswith("--") or not len(argn) > 2:
                logger.error("Cannot parse extra argument not provided by explicit long name with '--': %s", argn)
                sys.exit(1)
            argn = argn[2:].replace("-", "_")
            for arg_valid in [float_validator, int_validator, bool_validator]:
                try:
                    argv = arg_valid(argv)
                    break
                except PydanticTypeError:
                    pass
            xargs[argn] = argv
    logger.debug("Resolved extra arguments: %s", xargs)
    return xargs


def main(**args):
    parser = argparse.ArgumentParser(prog="blockchain", description="Blockchain Node Web Application")
    parser.add_argument("-p", "--port", default=5000, type=int, help="Port to listen on.")
    parser.add_argument("-H", "--host", default="0.0.0.0", help="Host to employ (can include protocol scheme).")
    parser.add_argument("-n", "--node", help="Unique identifier of the node. Generate one if omitted.")
    parser.add_argument("-N", "--nodes", nargs="*", action="append", type=str,
                        help="Node endpoints the blockchains should resolve consensus against.")
    parser.add_argument("-s", "--secret", required=True, help="Node secret for hash encryption.")

    db_args = parser.add_argument_group(title="Database", description="Database options.")
    db_args.add_argument("--db", "--database", required=True, action=DatabaseTypeAction,
                         help="Database to use. Formatted as [type://connection-detail].")
    db_args.add_argument("--new", action="store_true", help="Generate the new blockchain with genesis block.")

    log_args = parser.add_argument_group(title="Logger", description="Logging control.")
    level_args = log_args.add_mutually_exclusive_group()
    level_args.add_argument("-q", "--quiet", action="store_true", help="Disable logging except errors.")
    level_args.add_argument("-d", "--debug", action="store_true",
                            help="Debug level logging. This also enables error traceback outputs in responses.")
    log_args.add_argument("-v", "--verbose", action="store_true", help="Enforce verbose logging to stdout.")
    log_args.add_argument("-l", "--log", help="output file to write generated logs.")

    ns, argv = parser.parse_known_args(args=args or None)

    # set full module config
    level = logging.DEBUG if ns.debug else logging.ERROR if ns.quiet else logging.ERROR
    logger = set_logger_config(LOGGER, level=level, force_stdout=ns.verbose, file=ns.log)
    kwargs = parse_xargs(argv, logger)
    run(level=level, logger=logger, app=True, secret=ns.secret, new=ns.new,
        host=ns.host, port=ns.port, db=ns.db, node=ns.node, nodes=ns.nodes, **kwargs)


def run(host="0.0.0.0",         # type: str
        port=5001,              # type: int
        db=None,                # type: Union[str, Database]
        node=None,              # type: AnyUUID
        nodes=None,             # type: Union[str, List[str], List[List[str]]]
        new=False,              # type: bool
        secret=None,            # type: str
        level=logging.INFO,     # type: Union[int, str]
        logger=None,            # type: Optional[logging.Logger]
        app=False,              # type: bool
        **kwargs,               # type: Dict[str, Any]
        ):                      # type: (...) -> Optional[BlockchainWebApp]

    if isinstance(level, str):
        level = logging.getLevelName(level.upper())
    if not logger:
        logger = set_logger_config(LOGGER, level)
    if level == logging.DEBUG:
        APP.debug = True

    if not secret:
        logger.error("Missing required secret.")
        sys.exit(-1)
    APP.secret = secret

    try:
        node_id = node if node else str(uuid.uuid4())
        APP.node = Node(id=node_id, url=f"{host}:{port}")
        APP.db = db if isinstance(db, Database) else DatabaseTypeAction.get_db(db)

        if new:
            chain = Blockchain()
            logger.info("New blockchain: [%s]", chain.id)
            APP.db.save_chain(chain)
            sys.exit(0)

        # Generate a globally unique address for this node
        APP.blockchains = APP.db.load_multi_chain()
        if nodes:
            if isinstance(nodes, str):
                nodes = [nodes.split(",") if "," in nodes else nodes.split(" ") if " " in nodes else [nodes]]
            nodes = {node for node_list in nodes for node in node_list}  # flatten repeated -N, multi-URI per -N
            APP.nodes = list(sorted([Node(node) for node in nodes], key=lambda n: n.url))
            for node_ref in APP.nodes:
                if urlparse(node_ref.url) == urlparse(APP.node.url):
                    raise ValueError("Cannot use current APP endpoint as other consensus node endpoint.")
        if app:
            server = Server(
                Config(
                    APP,
                    host=host,
                    port=port,
                    log_level=level,
                    reload=True,
                    **kwargs
                ),
            )
            server.run()
        else:
            return APP  # for gunicorn
    except Exception as exc:
        logger.error("Unhandled error: %s", exc, exc_info=exc)
        sys.exit(-1)


if __name__ == "__main__":
    main()
