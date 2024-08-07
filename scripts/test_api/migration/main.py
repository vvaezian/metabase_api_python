"""
Migrates a collection.
"""
import argparse
import logging
import os
import re

from metabase_api.metabase_api import Metabase_API
from metabase_api.migration import migrate_collection
from metabase_api.utility import logger
from metabase_api.utility.db.tables import Src2DstEquivalencies
from metabase_api.utility.translation import Language

_logger = logging.getLogger(__name__)


RE_EMAIL = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def email_type(value):
    if not RE_EMAIL.match(value):
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid email")
    return value


if __name__ == "__main__":
    logger.setup(hint_opt="migration_api")
    _logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Collection migration",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-u", "--user", required=False, type=email_type, help="email address of user"
    )
    parser.add_argument(
        "-f", "--from", required=True, type=str, help="collection name to migrate"
    )
    parser.add_argument(
        "--db_target", required=True, type=str, help="name of target database"
    )
    # parser.add_argument("--db", type=ast.literal_eval, help="table mapping")
    parser.add_argument(
        "--to_parent", required=True, type=int, help="target parent collection id"
    )
    parser.add_argument(
        "-t", "--to", required=True, type=str, help="target collection name"
    )
    parser.add_argument("--name", required=True, type=str, help="new dashboard name")
    parser.add_argument(
        "--about", required=False, type=str, help="new dashboard 'about' section"
    )
    parser.add_argument(
        "--lang",
        choices=[l.name for l in Language],
        required=False,
        default=Language.EN.name,
    )

    args = parser.parse_args()
    config = vars(args)

    # if user's email wasn't specified, I need to find it as an env variable
    if not config["user"]:
        config["user"] = os.environ.get("METABASE_LOGIN")
        if not config["user"]:
            raise ValueError(
                "User's email not specified and not found in env variable METABASE_LOGIN"
            )
        _logger.info(f"Read {config['user']} from env variable METABASE_LOGIN")
    else:
        _logger.info("User's email can be stored in env variable METABASE_LOGIN")
    # is user's passwd kept as an env variable?
    user_passwd = os.environ.get("METABASE_PASSWD")
    if user_passwd is not None:
        _logger.info(
            f"Read of passwd for {config['user']} from env variable METABASE_PASSWD"
        )
    _logger.info(f"Turning on metabase API...")
    metabase_api = Metabase_API(
        "https://assistiq.metabaseapp.com", email=config["user"], password=user_passwd
    )
    # let's do it!
    # convert 'db_target' name to id
    db_target_id = metabase_api.get_item_id(
        item_type="database", item_name=config["db_target"]
    )
    table_equivalencies: Src2DstEquivalencies = Src2DstEquivalencies(
        metabase_api=metabase_api, dst_bd_id=db_target_id
    )
    # convert 'from' name to id
    src_collection_id = metabase_api.get_item_id(
        item_type="collection", item_name=config["from"]
    )
    # translating to a language other than English?
    target_lang = Language[args.lang]
    if target_lang != Language.EN:
        _logger.info(f"Translating to {target_lang.name}")
    _logger.info(f"Starting migration of collection {src_collection_id}")
    migrate_collection(
        metabase_api=metabase_api,
        lang=target_lang,
        source_collection_id=src_collection_id,
        db_target=db_target_id,
        parent_collection_id=config["to_parent"],
        destination_collection_name=config["to"],
        new_dashboard_description=config["about"],
        new_dashboard_name=config["name"],
        table_equivalencies=table_equivalencies,
    )
    # except Exception as e:
    #     _logger.error(f"Dashboard not properly migrated!: {str(e)}")
    #     r = metabase_api.put("/api/collection/{}".format(dashboard_id), json=dash)
    #     # todo: delete the destination collection, since it's not valid
