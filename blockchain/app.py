import argparse
import uuid
import logging
import sys
from urllib.parse import urlparse

from blockchain.api import APP
from blockchain.database import DB_TYPES, Database
from blockchain.impl import Blockchain, Node
from blockchain.utils import get_logger, set_logger_config

LOGGER = get_logger("blockchain")


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


def main(**args):
    parser = argparse.ArgumentParser(prog="blockchain", description="Blockchain Node Web Application")
    parser.add_argument("-p", "--port", default=5000, type=int, help="port to listen on")
    parser.add_argument("-n", "--node", help="Unique identifier of the node. Generate one if omitted.")
    parser.add_argument("-N", "--nodes", nargs="*", action="append", type=str,
                        help="Node endpoints the blockchains should resolve consensus against.")

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
    args = parser.parse_args(args=args)

    # set full module config
    level = logging.DEBUG if args.debug else logging.ERROR if args.quiet else logging.ERROR
    logger = set_logger_config(LOGGER, level=level, force_stdout=args.verbose, file=args.log)
    run_args = {"host": args.host, "port": args.port}
    run(level=level, host=args.host, port=args.port, db=args.db, node=args.node, nodes=args.nodes, new=args.new,
        logger=logger, **run_args)


def run(host="0.0.0.0", port=5001, db=None, node=None, nodes=None, new=False,
        level=logging.INFO, logger=None, **run_args):

    if isinstance(level, str):
        level = logging.getLevelName(level.upper())
    if not logger:
        logger = set_logger_config(LOGGER, level)
    if level == logging.DEBUG:
        APP.debug = True

    try:
        APP.url = f"http://{host}:{port}"
        APP.db = db if isinstance(db, Database) else DatabaseTypeAction.get_db(db)

        if new:
            chain = Blockchain()
            logger.info("New blockchain: [%s]", chain.id)
            APP.db.save_chain(chain)
            sys.exit(0)

        # Generate a globally unique address for this node
        APP.node = node if node else str(uuid.uuid4())
        APP.blockchains = APP.db.load_multi_chain()
        if nodes:
            if isinstance(nodes, str):
                nodes = [nodes.split(",") if "," in nodes else nodes.split(" ") if " " in nodes else [nodes]]
            nodes = {node for node_list in nodes for node in node_list}  # flatten repeated -N, multi-URI per -N
            APP.nodes = list(sorted([Node(node) for node in nodes], key=lambda n: n.url))
            for node_ref in APP.nodes:
                if urlparse(node_ref.url) == urlparse(APP.url):
                    raise ValueError("Cannot use current APP endpoint as other consensus node endpoint.")
        if run_args:
            APP.run(**run_args)
        else:
            return APP
    except Exception as exc:
        logger.error("Unhandled error: %s", exc, exc_info=exc)
        sys.exit(-1)


if __name__ == "__main__":
    main()
