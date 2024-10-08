import logging
from typing import Optional, Collection

from metabase_api import Metabase_API
from metabase_api._helper_methods import ItemType
from metabase_api.objects.collection import Collection
from metabase_api.objects.defs import CardParameters
from metabase_api.utility.db.tables import TablesEquivalencies
from metabase_api.utility.options import Options

_logger = logging.getLogger(__name__)


def _do_copy_collection(
    metabase_api: Metabase_API,
    source_collection_id: int,
    parent_collection_id: int,
    destination_collection_name: str,
) -> dict[str, dict[int, int]]:
    source_collection_name = metabase_api.get_item_name(
        item_type="collection", item_id=source_collection_id
    )
    _logger.info(f"source_collection_name = '{source_collection_name}'")

    # let's copy the collection inside a (manually chosen) parent collect
    parent_collection_name = metabase_api.get_item_name(
        item_type="collection", item_id=parent_collection_id
    )
    _logger.info(
        f"parent collection for target=id:{parent_collection_id}, name: '{parent_collection_name}'"
    )
    # all good
    _logger.debug(
        f"ok. Let's now copy {source_collection_id} as a kid of {parent_collection_id}..."
    )
    transformations = metabase_api.copy_collection(
        source_collection_id=source_collection_id,
        destination_parent_collection_id=parent_collection_id,
        destination_collection_name=destination_collection_name,
        deepcopy_dashboards=True,
    )
    return transformations


def migrate_collection(
    metabase_api: Metabase_API,
    source_collection_id: int,
    db_target: int,
    parent_collection_id: int,
    destination_collection_name: str,
    table_equivalencies: TablesEquivalencies,
    user_options: Options,
    new_dashboard_description: Optional[str] = None,
    new_dashboard_name: Optional[str] = None,
):
    transformations = _do_copy_collection(
        metabase_api,
        source_collection_id=source_collection_id,
        parent_collection_id=parent_collection_id,
        destination_collection_name=destination_collection_name,
    )
    _logger.info(f"'{source_collection_id}' duplicated - now starts the migration")
    card_params = CardParameters(
        metabase_api=metabase_api,
        db_target=db_target,
        transformations=transformations,
        table_equivalencies=table_equivalencies,
        personalization_options=user_options,
    )
    dst_collection_id = metabase_api.get_item_id(
        item_type=ItemType.COLLECTION,
        item_name=destination_collection_name,
        collection_name=destination_collection_name,
    )
    dst_collection = Collection.from_id(
        coll_id=dst_collection_id, metabase_api=metabase_api
    )
    assert dst_collection.migrate(params=card_params, push=False)

    if len(card_params.personalization_options.labels_replacements) > 0:
        _logger.info(f"Replacing collection {dst_collection_id}'s labels ...")
        dst_collection.translate(
            translation_dict=card_params.personalization_options.labels_replacements
        )
        # dst_collection.push(metabase_api=metabase_api)

    _logger.info("Migration successfully completed.")
