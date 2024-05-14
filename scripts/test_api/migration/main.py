"""
Migrates a collection.
"""
import argparse
import ast

import logging

from metabase_api.metabase_api import Metabase_API
from metabase_api.migration import migrate_collection

from metabase_api.utility import logger

_logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.setup()
    _logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Collection migration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
    parser.add_argument("--title", required=True, type=str, help="new dashboard title")
    parser.add_argument(
        "--about", required=False, type=str, help="new dashboard 'about' section"
    )

    args = parser.parse_args()
    config = vars(args)

    metabase_api = Metabase_API(
        "https://assistiq.metabaseapp.com", "wafa@assistiq.ai", "AssistIQ2023."
    )
    # try:
    migrate_collection(
        metabase_api=metabase_api,
        source_collection_id=config["from"],
        db_target=config["db_target"],
        parent_collection_id=config["to_parent"],
        destination_collection_name=config["to"],
        table_src2dst=config["tables"],
        new_dashboard_name=config["title"],
        new_dashboard_description=config["about"],
    )
    # except Exception as e:
    #     _logger.error(f"Dashboard not properly migrated!: {str(e)}")
    #     r = metabase_api.put("/api/collection/{}".format(dashboard_id), json=dash)
    #     # todo: delete the destination collection, since it's not valid
