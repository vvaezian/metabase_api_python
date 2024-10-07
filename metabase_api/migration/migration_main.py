import logging
from typing import Optional

from metabase_api import Metabase_API
from metabase_api._helper_methods import ItemType
from metabase_api.objects.card import Card
from metabase_api.objects.dashboard import Dashboard
from metabase_api.objects.defs import CardParameters
from metabase_api.utility.db.tables import TablesEquivalencies
from metabase_api.utility.options import Options
from metabase_api.utility.translation import (
    Language,
    Translators,
)

_logger = logging.getLogger(__name__)


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
    _logger.info(f"'{source_collection_id}' duplicated - now starts the migration")
    dst_collection_id = metabase_api.get_item_id(
        item_type=ItemType.COLLECTION,
        item_name=destination_collection_name,
        collection_name=destination_collection_name,
    )
    # get all collection items
    collections_ids_to_visit: list[int] = [dst_collection_id]
    items: list[dict] = []
    while len(collections_ids_to_visit) > 0:
        coll_id = collections_ids_to_visit[0]
        collections_ids_to_visit = collections_ids_to_visit[1:]
        collection_details = metabase_api.get(f"/api/collection/{coll_id}/items")
        collection_items = collection_details["data"]
        # are there sub-collections in this collection?
        if "collection" in collection_details["models"]:
            # we need to collect the items recursively
            sub_collections = [
                item["id"] for item in collection_items if item["model"] == "collection"
            ]
            collections_ids_to_visit = collections_ids_to_visit + sub_collections
        # I won't need to visit the collections themselves anymore:
        items = items + [
            item for item in collection_items if item["model"] != "collection"
        ]

    # first we migrate cards
    card_params = CardParameters(
        metabase_api=metabase_api,
        db_target=db_target,
        transformations=transformations,
        table_equivalencies=table_equivalencies,
        personalization_options=user_options,
    )
    card_items = [item for item in items if item["model"] == "card"]
    for item in card_items:
        # nb: I can't do this
        # r = Card(card_json=item).migrate(card_params)
        # because not _all_ info is there. Need to fetch it again:
        r = Card.from_id(card_id=item["id"], metabase_api=metabase_api).migrate(
            params=card_params, push=True
        )
        if not r:
            raise RuntimeError(f"Impossible to migrate card '{item['id']}'")
    # and now we migrate dashboards
    dashboard_items = [item for item in items if item["model"] == "dashboard"]
    if (len(dashboard_items) == 0) and (new_dashboard_description is not None):
        _logger.warning(
            f"Dashboard description specified ('{new_dashboard_description}') but no dashboard present in the collection."
        )
    for item in dashboard_items:
        dashboard_id = item["id"]
        _logger.info(f"Obtaining details of dashboard {dashboard_id}...")
        dash = metabase_api.get(f"/api/dashboard/{dashboard_id}")
        if dash["archived"]:
            _logger.info(f"Dashboard {dashboard_id} is archived. Will migrate anyways.")
        _logger.info(f"Migrating dashboard {dashboard_id}...")
        dashboard = Dashboard(dash)
        dashboard.migrate(params=card_params, push=False)
        dashboard.translate(
            translation_dict=card_params.personalization_options.labels_replacements
        )
        assert dashboard.push(
            metabase_api
        ), f"Problems updating dashboard '{dashboard_id}'"
    _logger.info("Migration terminated")
