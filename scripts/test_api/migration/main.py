"""
Migrates a collection.
"""
import argparse
import ast
import re

import logging

from metabase_api.metabase_api import Metabase_API
from metabase_api.migration import migrate_collection

from metabase_api.utility import logger

_logger = logging.getLogger(__name__)


RE_EMAIL = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def email_type(value):
    if not RE_EMAIL.match(value):
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid email")
    return value


if __name__ == "__main__":
    logger.setup()
    _logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Collection migration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-u", "--user", required=True, type=email_type, help="email address of user"
    )
    parser.add_argument(
        "-f", "--from", required=True, type=int, help="id for session to migrate"
    )
    parser.add_argument(
        "--db_target", required=True, type=int, help="id for database target"
    )
    parser.add_argument("--tables", type=ast.literal_eval, help="table mapping")
    parser.add_argument(
        "--to_parent", required=True, type=int, help="target parent collection id"
    )
    parser.add_argument(
        "-t", "--to", required=True, type=str, help="target collection name"
    )
    parser.add_argument(
        "--about", required=False, type=str, help="new dashboard 'about' section"
    )

    args = parser.parse_args()
    config = vars(args)

    metabase_api = Metabase_API("https://assistiq.metabaseapp.com", config["user"])
    # try:
    migrate_collection(
        metabase_api=metabase_api,
        source_collection_id=config["from"],
        db_target=config["db_target"],
        parent_collection_id=config["to_parent"],
        destination_collection_name=config["to"],
        table_src2dst=config["tables"],
        new_dashboard_description=config["about"],
    )
    # except Exception as e:
    #     _logger.error(f"Dashboard not properly migrated!: {str(e)}")
    #     r = metabase_api.put("/api/collection/{}".format(dashboard_id), json=dash)
    #     # todo: delete the destination collection, since it's not valid
