"""
Migrates a collection.
"""
import argparse
import ast

from metabase_api.metabase_api import Metabase_API
from metabase_api.migration import migrate_collection

if __name__ == "__main__":
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

    args = parser.parse_args()
    config = vars(args)

    migrate_collection(
        metabase_api=Metabase_API(
            "https://assistiq.metabaseapp.com", "wafa@assistiq.ai", "AssistIQ2023."
        ),
        source_collection_id=config["from"],
        db_target=config["db_target"],
        PARENT_COLLECTION_ID=config["to_parent"],
        destination_collection_name=config["to"],
        table_src2dst=config["tables"],
    )
