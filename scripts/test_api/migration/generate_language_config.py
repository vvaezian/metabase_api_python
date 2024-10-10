"""
Given a language, generates a config for it.
"""
import argparse
import json
import logging
import os
from pathlib import Path

from metabase_api._helper_methods import ItemType
from metabase_api.metabase_api import Metabase_API
from metabase_api.objects.collection import Collection
from metabase_api.utility import logger
from metabase_api.utility.translation import Language, Translators
from metabase_api.utility.util import email_type

_logger = logging.getLogger(__name__)


def _email_type(value: str) -> str:
    if not email_type(value):
        raise argparse.ArgumentTypeError(f"'{value}' is not a valid email")
    return value


if __name__ == "__main__":
    logger.setup(hint_opt="language_config")
    _logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Generates config file for a specific language.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-u", "--user", required=False, type=_email_type, help="email address of user"
    )
    parser.add_argument(
        "-f",
        "--from",
        required=True,
        type=str,
        help="collection name to take as a starting point",
    )
    parser.add_argument(
        "--language",
        required=True,
        type=str,
        choices=[l.name for l in Language if l != Language.EN],
        help="to what language",
    )
    parser.add_argument(
        "-t", "--to", required=True, type=Path, help="file to be written"
    )

    args = parser.parse_args()
    config = vars(args)

    # do I have a translator for that language?
    target_lang = Language[config["language"]]
    if target_lang not in Translators:
        raise NotImplementedError(f"Translator for '{target_lang}' unavailable")
    translator = Translators[target_lang]
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
    _logger.info(f"Turning metabase API on...")
    metabase_api = Metabase_API(
        "https://assistiq.metabaseapp.com", email=config["user"], password=user_passwd
    )
    # let's do it!
    # convert 'from' name to id
    src_collection_name = config["from"]
    src_collection_id = metabase_api.get_item_id(
        item_type=ItemType.COLLECTION, item_name=src_collection_name
    )
    destination_config_file = config["to"]

    english_labels: set[str] = Collection.from_id(
        src_collection_id, metabase_api=metabase_api
    ).labels
    # let's translate all these labels
    translation_dict: dict[str, str] = {
        in_english: translator.translate(in_english) for in_english in english_labels
    }
    # and let's also make sure we don't miss any of the user-defined labels
    # (even if they don't appear in the collection we took as sample)
    size_bef = len(translation_dict)
    translation_dict = translation_dict | translator.user_defined_terms
    _logger.info(
        f"Added {len(translation_dict) - size_bef} user-defined terms NOT found on source"
    )
    #
    _logger.info(f"Saving dictionary to '{config['to']}'...")
    with open(config["to"], "w") as fp:
        json.dump(translation_dict, fp, sort_keys=True, indent=2, ensure_ascii=False)
    _logger.info("done!")
