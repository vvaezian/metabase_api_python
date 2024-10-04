import logging
from copy import deepcopy
from typing import Optional

from metabase_api import Metabase_API
from metabase_api._helper_methods import ItemType
from metabase_api.objects.card import Card
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
            params=card_params
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
        # let's visit all of its parts - to translate or to update references
        for card_json in dash["dashcards"]:
            Card(card_json).migrate(card_params, push=False)
        for k, v in dash.items():
            if k == "description":
                if dash["description"] is not None:
                    dash["description"] = user_options.maybe_replace_label(
                        dash["description"]
                    )
            elif k == "tabs":
                # tabs in dashboard
                tabs = v
                for a_tab in tabs:
                    # let's translate the name
                    a_tab["name"] = user_options.maybe_replace_label(a_tab["name"])
            elif k == "parameters":
                parameters = v
                for params_dict in parameters:
                    # let's translate the name
                    params_dict["name"] = user_options.maybe_replace_label(
                        params_dict["name"]
                    )
                    # and now let's update all references
                    if params_dict.get("values_source_type", "nothing") == "card":
                        src_config = params_dict["values_source_config"]
                        src_config["card_id"] = transformations["cards"][
                            src_config["card_id"]
                        ]
                        if "value_field" in src_config:
                            value_field = src_config["value_field"]
                            if value_field[0] == "field":
                                if isinstance(value_field[1], int):
                                    value_field[
                                        1
                                    ] = table_equivalencies.column_equivalent_for(
                                        column_id=value_field[1]
                                    )
            elif k == "param_values":
                param_values = v
                if param_values is not None:
                    for field_id_as_str, field_info in deepcopy(
                        dash["param_values"]
                    ).items():
                        field_id = int(field_id_as_str)
                        # was it already migrated?
                        if (
                            card_params.table_equivalencies.target_table_for_column(
                                column_id=field_id
                            )
                            is None
                        ):
                            new_field_id = card_params.replace_column_id(
                                column_id=field_id
                            )
                            # by any chance, is this column _already_ on a target table?
                            if (
                                card_params.table_equivalencies.target_table_for_column(
                                    column_id=new_field_id
                                )
                                is None
                            ):
                                # no, it's not already migrated. Carry on!
                                new_field_id_as_str = str(new_field_id)
                                param_values[new_field_id_as_str] = param_values.pop(
                                    field_id_as_str
                                )
                                param_values[new_field_id_as_str][
                                    "field_id"
                                ] = new_field_id
                                param_values[new_field_id_as_str]["values"] = list()
            elif k == "param_fields":
                # param fields
                old_param_fields = deepcopy(dash["param_fields"])
                if old_param_fields is not None:
                    for field_id_as_str, field_info in old_param_fields.items():
                        try:
                            field_id = int(field_id_as_str)
                            # if this field is _already_ on the target tables, no need to migrate it:
                            if (
                                table_equivalencies.target_table_for_column(
                                    column_id=field_id
                                )
                                is None
                            ):
                                src_table_id = field_info["table_id"]
                                field_name = table_equivalencies.get_src_table(
                                    table_id=src_table_id
                                ).get_column_name(column_id=field_id)
                                dst_table_id = table_equivalencies[
                                    src_table_id
                                ].unique_id
                                new_field_id = table_equivalencies.get_dst_table(
                                    dst_table_id
                                ).get_column_id(field_name)
                                # ok. Let's now change:
                                new_field_id_as_str = str(new_field_id)
                                dash["param_fields"][new_field_id_as_str] = dash[
                                    "param_fields"
                                ].pop(field_id_as_str)
                                dash["param_fields"][new_field_id_as_str][
                                    "id"
                                ] = new_field_id_as_str
                                dash["param_fields"][new_field_id_as_str][
                                    "table_id"
                                ] = dst_table_id
                        except ValueError as ve:
                            # apparently one of the param fields is not an int...?
                            pass
            elif k == "name":
                # change name, tag it, and go!
                dash["name"] = (
                    new_dashboard_name
                    if new_dashboard_name is not None
                    else dash["name"]
                )
            elif k == "description":
                # change description
                dash["description"] = (
                    new_dashboard_description
                    if new_dashboard_description is not None
                    else dash["description"]
                )
        _logger.info(f"Using API to update dashboard '{dashboard_id}'...")
        r = metabase_api.put(f"/api/dashboard/{dashboard_id}", json=dash)
        # sanity check
        assert r == 200, f"Problems updating dashboard '{dashboard_id}'; code {r}"
    _logger.info("Migration terminated")
