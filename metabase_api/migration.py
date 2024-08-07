import logging
from copy import deepcopy
from typing import Optional, Any

from metabase_api import Metabase_API
from metabase_api.utility.db.tables import Src2DstEquivalencies
from metabase_api.utility.translation import (
    Language,
    Translators,
)

MIGRATED_CARDS: list[int] = list()

_logger = logging.getLogger(__name__)


def _translate_card(card_json: dict, lang: Language) -> dict:
    """
    Translates a card, on its totality.
    Args:
        card_json:

    Returns:

    """
    for k, v in card_json.items():
        if (k == "description") or (k == "name"):
            if v is not None:
                card_json[k] = Translators[lang].translate(v)
        elif k == "visualization_settings":
            viz_set = v
            for k, v in viz_set.items():
                if k.endswith("title_text"):
                    viz_set[k] = Translators[lang].translate(v)
                elif "text" in k:
                    viz_set[k] = Translators[lang].translate(v)
                elif (k == "graph.metrics") or (k == "pie.metric"):
                    _logger.debug(
                        f"[visualization_settings] anything I have to do for '{k}'...? (value is '{v}')"
                    )
                elif k == "column_settings":
                    cols_set = viz_set["column_settings"]
                    for _, d in cols_set.items():
                        for k, v in d.items():
                            if k == "column_title":
                                d[k] = Translators[lang].translate(v)
                            else:
                                _logger.debug(
                                    f"[visualization_settings][column_settings] '{k}': I guess I do nothing? (value is '{v}')"
                                )
                elif k == "series_settings":
                    series_set = viz_set["series_settings"]
                    for _, d in series_set.items():
                        for k, v in d.items():
                            if k == "title":
                                d[k] = Translators[lang].translate(v)
                            else:
                                _logger.debug(
                                    f"[visualization_settings][series_settings] '{k}': I guess I do nothing? (value is '{v}')"
                                )
                elif k.endswith("column") or k.endswith("columns"):
                    _logger.debug(
                        f"[visualization_settings]['{k}']: accesses column names so I don't think we need to change anything (value is '{v}')"
                    )
                else:
                    _logger.debug(
                        f"[visualization_settings]['{k}'] is it possible there is nothing to do? (value is '{v}')"
                    )
        # elif k == 'parameter_mappings':
        #     print("lala")
        # elif k == 'parameters':
        #     print("lala")
        # else:
        #     print(f"[{k}] Anything else to translate?")
    return card_json


def migrate_card_by_id(
    card_id: int,
    lang: Language,
    metabase_api: Metabase_API,
    db_target: int,
    transformations,
    table_equivalencies: Src2DstEquivalencies,
) -> bool:
    if card_id in MIGRATED_CARDS:
        _logger.debug(f"[already migrated card id '{card_id}']")
        return True
    _logger.info(f"Visiting card id '{card_id}'")
    card_json = metabase_api.get(f"/api/card/{card_id}")
    # translate to specific language
    # card_json = _translate_card(card_json, lang=lang)
    # update db and table id
    # db
    card_json["database_id"] = db_target
    card_json["dataset_query"]["database"] = db_target
    # table
    table_id = card_json["table_id"]
    if table_id is not None:
        try:
            card_json["table_id"] = table_equivalencies[table_id].unique_id
        except KeyError as ke:
            # mmmh... by any chance is this table_id already in target?
            # (in which case it would mean that it had already been replaced)
            if table_id not in table_equivalencies.dst_tables_ids:
                msg = f"[re-writing references on card '{card_id}']"
                msg += f"Table '{table_id}' is referenced at source, but no replacement is specified."
                raise ValueError(msg) from ke
        # and now I have to replace the fields' references to this table
        # these next 2 lines were not used. Commenting them as I don't understand what's up. todo: delete?
        # src_table_fields = column_references["src"][table_id]
        # dst_table_fields = column_references["dst"][table_src2dst[table_id]]
    # change result metadata
    if ("result_metadata" not in card_json) or (card_json["result_metadata"] is None):
        _logger.debug(f"[card: {card_id}] There is no 'result_metadata'")
    else:
        for md in card_json["result_metadata"]:
            if ("field_ref" in md) and (md["field_ref"][0] == "field"):
                old_field_id = md["field_ref"][1]
                if isinstance(old_field_id, int):
                    new_field_id = table_equivalencies.find_field_destination(
                        old_field_id=old_field_id
                    )
                    # awesomeness!
                    md["field_ref"][1] = new_field_id
                    md["id"] = new_field_id
            if "table_id" in md:
                md["table_id"] = table_equivalencies[table_id].unique_id
    # change query
    if "query" in card_json["dataset_query"]:
        query_part = card_json["dataset_query"]["query"]
        # if "source-table" in query_part:
        update_query_part(
            card_id=card_id,
            lang=lang,
            query_part=query_part,
            table_equivalencies=table_equivalencies,
            cards_src2dst=transformations["cards"],
            metabase_api=metabase_api,
            db_target=db_target,
            transformations=transformations,
        )
    handle_card(
        card_json,
        lang=lang,
        table_equivalencies=table_equivalencies,
        transformations=transformations,
        db_target=db_target,
    )
    # and go!
    success = metabase_api.put("/api/card/{}".format(card_id), json=card_json) == 200
    if success:
        MIGRATED_CARDS.append(card_id)
    return success


def migrate_card(
    item: dict,
    lang: Language,
    metabase_api: Metabase_API,
    db_target: int,
    table_equivalencies: Src2DstEquivalencies,
    # column_references: dict[str, dict[int, ColumnReferences]],
    transformations,
    # table_src2dst: Optional[dict[int, int]] = None,
) -> bool:
    assert (
        item["model"] == "card"
    ), f"Trying to migrate a card that is NOT actually a card: it is a '{item['model']}'"
    return migrate_card_by_id(
        card_id=item["id"],
        lang=lang,
        metabase_api=metabase_api,
        db_target=db_target,
        table_equivalencies=table_equivalencies,
        transformations=transformations,
    )


def migrate_collection(
    metabase_api: Metabase_API,
    source_collection_id: int,
    db_target: int,
    parent_collection_id: int,
    destination_collection_name: str,
    table_equivalencies: Src2DstEquivalencies,
    lang: Language,
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
    # if the destination collection already exists, fail
    _logger.debug(
        f"Checking that the destination collection '{destination_collection_name}' doesn't already exist..."
    )
    try:
        _ = metabase_api.get_item_id(
            item_type="collection",
            item_name=destination_collection_name,
            collection_name=destination_collection_name,
        )
        raise RuntimeError(f"Collection '{destination_collection_name}' exists")
    except ValueError as ve:
        # if I am here it's because the collection doesn't exist - which is exactly what I want
        pass
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
        item_type="collection",
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
    card_items = [item for item in items if item["model"] == "card"]
    for item in card_items:
        r = migrate_card(
            lang=lang,
            metabase_api=metabase_api,
            item=item,
            db_target=db_target,
            table_equivalencies=table_equivalencies,
            # column_references=column_references,
            transformations=transformations,
            # table_src2dst=table_src2dst,
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
        for k, v in dash.items():
            if k == "description":
                dash["description"] = Translators[lang].translate(dash["description"])
            elif k == "tabs":
                # tabs in dashboard
                tabs = v
                for a_tab in tabs:
                    # let's translate the name
                    a_tab["name"] = Translators[lang].translate(a_tab["name"])
            elif k == "parameters":
                parameters = v
                for params_dict in parameters:
                    # let's translate the name
                    params_dict["name"] = Translators[lang].translate(
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
                                    ] = table_equivalencies.find_field_destination(
                                        old_field_id=value_field[1]
                                    )
            elif k == "param_values":
                param_values = v
                if param_values is not None:
                    for field_id_as_str, field_info in deepcopy(
                        dash["param_values"]
                    ).items():
                        field_id = int(field_id_as_str)
                        new_field_id = table_equivalencies.find_field_destination(
                            old_field_id=field_id
                        )
                        new_field_id_as_str = str(new_field_id)
                        param_values[new_field_id_as_str] = param_values.pop(
                            field_id_as_str
                        )
                        param_values[new_field_id_as_str]["field_id"] = new_field_id
            elif k == "param_fields":
                # param fields
                old_param_fields = deepcopy(dash["param_fields"])
                if old_param_fields is not None:
                    for field_id_as_str, field_info in old_param_fields.items():
                        try:
                            field_id = int(field_id_as_str)
                            src_table_id = field_info["table_id"]
                            field_name = table_equivalencies.get_src_table(
                                table_id=src_table_id
                            ).get_column_name(column_id=field_id)
                            dst_table_id = table_equivalencies[src_table_id].unique_id
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
            elif k == "dashcards":
                for card_json in dash["dashcards"]:
                    handle_card(
                        card_json,
                        lang=lang,
                        table_equivalencies=table_equivalencies,
                        transformations=transformations,
                        db_target=db_target,
                    )
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


def handle_card(
    card_json,
    lang: Language,
    table_equivalencies: Src2DstEquivalencies,
    transformations,
    db_target: int,
):
    # todo: this...?
    _translate_card(card_json, lang=lang)
    # mappings to filters
    for mapping in card_json["parameter_mappings"]:
        if "card_id" in mapping:
            mapping["card_id"] = transformations["cards"][mapping["card_id"]]
        else:
            print("1")
        if "target" in mapping:
            t = mapping["target"]
            if (t[0] == "dimension") and (t[1][0] == "field"):
                if isinstance(t[1][1], int):
                    t[1][1] = table_equivalencies.find_field_destination(
                        old_field_id=t[1][1]
                    )
    if "visualization_settings" in card_json:
        update_viz_settings(
            viz_settings=card_json["visualization_settings"],
            lang=lang,
            table_equivalencies=table_equivalencies,
            transformations=transformations,
        )
    # card itself
    # Luis is not exactly sure this makes any difference :shrug: todo: revise
    if "card" in card_json:
        card = card_json["card"]
        if "table_id" in card:
            if card["table_id"] is not None:
                if card["table_id"] not in table_equivalencies.dst_tables_ids:
                    card["table_id"] = table_equivalencies[card["table_id"]].unique_id
        if "database_id" in card:
            if card["database_id"] != db_target:
                card["database_id"] = db_target


def update_viz_settings(
    viz_settings: dict,
    table_equivalencies: Src2DstEquivalencies,
    lang: Language,
    transformations,
):
    if "text" in viz_settings:
        viz_settings["text"] = Translators[lang].translate(viz_settings["text"])
    if "graph.x_axis.title_text" in viz_settings:
        viz_settings["graph.x_axis.title_text"] = Translators[lang].translate(
            viz_settings["graph.x_axis.title_text"]
        )
    if "series_settings" in viz_settings:
        ser_sets = viz_settings["series_settings"]
        for _, d in ser_sets.items():
            for k, v in d.items():
                if k == "title":
                    d[k] = Translators[lang].translate(v)
    if "table.columns" in viz_settings:
        for table_column in viz_settings["table.columns"]:
            update_table_cols_info(
                table_column,
                table_equivalencies=table_equivalencies,
            )
    if "column_settings" in viz_settings:
        # first, let's change keys (if needed)
        for k in deepcopy(viz_settings["column_settings"]).keys():
            # continue
            l = eval(k.replace("null", "None"))
            if l[0] == "ref":
                field_info = l[1]
                if field_info[0] == "field":
                    field_info[1] = table_equivalencies.find_field_destination(
                        old_field_id=field_info[1]
                    )
                    new_k = str(l).replace("None", "null").replace("'", '"')
                    viz_settings["column_settings"][new_k] = viz_settings[
                        "column_settings"
                    ].pop(k)
        for k, d in viz_settings["column_settings"].items():
            if "click_behavior" in d:
                click_behavior = d["click_behavior"]
                handle_click_behavior(
                    click_behavior=click_behavior,
                    table_equivalencies=table_equivalencies,
                    transformations=transformations,
                )
    if "click_behavior" in viz_settings:
        click_behavior = viz_settings["click_behavior"]
        handle_click_behavior(
            click_behavior=click_behavior,
            table_equivalencies=table_equivalencies,
            transformations=transformations,
        )


def handle_click_behavior(
    click_behavior: dict,
    table_equivalencies: Src2DstEquivalencies,
    transformations,
):
    if "targetId" in click_behavior:
        try:
            old_targetid = click_behavior["targetId"]
        except KeyError as ke:
            raise ValueError(f"no target id") from ke
        try:
            new_targetid = transformations["cards"][old_targetid]
        except KeyError:
            msg = f"Target '{old_targetid}' is referenced at source, but no replacement is specified."
            _logger.error(msg)
            raise RuntimeError(msg)
        click_behavior["targetId"] = new_targetid
    if "parameterMapping" in click_behavior:
        for mapping_name, mapping in deepcopy(
            click_behavior["parameterMapping"]
        ).items():
            # I can see fields in 'target'. # todo: are there some in 'source' too...?
            if "target" in mapping:
                map_target = mapping["target"]
                if map_target["type"] == "dimension":
                    map_target_dim = map_target["dimension"]
                    field_info = map_target_dim[1]
                    if field_info[0] == "field":
                        if isinstance(field_info[1], int):
                            field_info[1] = table_equivalencies.find_field_destination(
                                old_field_id=field_info[1]
                            )
                        map_target["id"] = str(map_target["dimension"])
                        old_id = mapping["id"]
                        mapping["id"] = map_target["id"]
                        click_behavior["parameterMapping"].pop(old_id)
                        click_behavior["parameterMapping"][mapping["id"]] = mapping


def update_table_cols_info(
    table_column: dict,
    table_equivalencies: Src2DstEquivalencies,
) -> dict:
    for key, value in table_column.items():
        if key == "fieldRef":
            field_ref = value  # table_column["fieldRef"]
            if field_ref[0] == "field":
                old_field_id = field_ref[1]
                if isinstance(old_field_id, int):
                    new_field_id = table_equivalencies.find_field_destination(
                        old_field_id=old_field_id
                    )
                    field_ref[1] = new_field_id
        elif key == "key":
            l = eval(value.replace("null", "None"))
            if l[0] == "ref":
                field_info = l[1]
                if field_info[0] == "field":
                    field_info[1] = table_equivalencies.find_field_destination(
                        old_field_id=field_info[1]
                    )
                    table_column[key] = (
                        str(l)
                        .replace("None", "null")
                        .replace("'", '"')
                        .replace(" ", "")
                    )
                    # new_k = str(l).replace("None", "null").replace("'", '"')
                    # viz_settings["column_settings"][new_k] = viz_settings[
                    #     "column_settings"
                    # ].pop(k)

    return table_column


def _replace_field_info_refs(
    field_info: list,
    table_equivalencies: Src2DstEquivalencies,
) -> list:
    if field_info[0] == "field":
        # reference to a table's column. Replace it.
        old_field_id = field_info[1]
        if isinstance(old_field_id, int):
            new_field_id = table_equivalencies.find_field_destination(
                old_field_id=old_field_id
            )
            # awesomeness!
            field_info[1] = new_field_id
    else:
        for idx, item in enumerate(field_info):
            if isinstance(item, list):
                field_info[idx] = _replace_field_info_refs(
                    item,
                    table_equivalencies=table_equivalencies,
                )
    return field_info


def update_query_part(
    card_id: int,
    lang: Language,
    query_part: dict,  # todo: be more specific!
    metabase_api: Metabase_API,
    db_target: int,
    transformations,
    cards_src2dst: dict[int, int],  # transformations['cards']
    table_equivalencies: Src2DstEquivalencies,
) -> tuple[dict, list[int]]:  # todo: be more specific!
    """change query."""

    # table
    if "source-table" in query_part:
        src_table_in_query = query_part["source-table"]
        if isinstance(src_table_in_query, int):
            # if the source is an int => it MUST be the id of a table
            # (and so its correspondence must be found in the input)
            try:
                query_part["source-table"] = table_equivalencies[
                    src_table_in_query
                ].unique_id
            except KeyError as ke:
                msg = f"[re-writing references on card '{card_id}']"
                msg += f"Table '{src_table_in_query}' is referenced at source, but no replacement is specified."
                raise ValueError(msg) from ke
            # # and now I have to replace the fields' references to this table
            # src_table_fields = column_references["src"][src_table_in_query]
            # dst_table_fields = column_references["dst"][
            #     table_src2dst[src_table_in_query]
            # ]
        elif str(src_table_in_query).startswith("card"):
            # it's reference a card. Which one?
            ref_card_id = int(src_table_in_query.split("__")[1])
            try:
                # when we find such reference, this referenced card MUST be migrated before the referencees cards:
                new_card_id = cards_src2dst[ref_card_id]
            except KeyError as ke:
                raise KeyError(
                    f"Card {ref_card_id} is referenced in dashboard but we can't find the card itself."
                ) from ke
            _logger.debug(f"=---- migrating referenced card '{new_card_id}'")
            migrate_card_by_id(
                card_id=new_card_id,
                lang=lang,
                metabase_api=metabase_api,
                db_target=db_target,
                table_equivalencies=table_equivalencies,
                transformations=transformations,
            )
            query_part["source-table"] = f"card__{new_card_id}"
        else:
            raise ValueError(
                f"I don't know what this reference is: {src_table_in_query}"
            )
    # query!
    if "source-query" in query_part:
        query_part["source-query"] = update_query_part(
            card_id=card_id,
            lang=lang,
            metabase_api=metabase_api,
            db_target=db_target,
            transformations=transformations,
            query_part=query_part["source-query"],
            cards_src2dst=cards_src2dst,
            table_equivalencies=table_equivalencies,
        )
    if "filter" in query_part:

        def handle_condition_filter(filter_parts: Any):
            # todo: do I need to return anything....?
            def _is_cmp_op(op: str) -> bool:
                # cmp operator (like '>', '=', ...)
                return (op == ">") or (op == "=") or (op == "<=>")

            if isinstance(filter_parts, list):
                op = filter_parts[0]
                if op == "field":
                    # reference to a table's column. Replace it.
                    field_info = filter_parts
                    old_field_id = field_info[1]
                    if isinstance(old_field_id, int):
                        new_field_id = table_equivalencies.find_field_destination(
                            old_field_id=old_field_id
                        )
                        # awesomeness!
                        field_info[1] = new_field_id
                elif (op == "or") or (op == "and"):
                    handle_condition_filter(filter_parts=filter_parts[1])
                    handle_condition_filter(filter_parts=filter_parts[2])
                elif _is_cmp_op(op):
                    handle_condition_filter(filter_parts=filter_parts[1])
                    handle_condition_filter(filter_parts=filter_parts[2])
                else:
                    print(f"Luis, this should be a constant: '{op}'... is it?")

        handle_condition_filter(filter_parts=query_part["filter"])
        #
        #
        # field_info = query_part["filter"][1]
        # if field_info[0] == "field":
        #     # reference to a table's column. Replace it.
        #     old_field_id = field_info[1]
        #     new_field_id = find_field_destination(
        #         old_field_id=old_field_id,
        #         column_references=column_references,
        #         table_src2dst=table_src2dst,
        #     )
        #     # awesomeness!
        #     field_info[1] = new_field_id
    if "aggregation" in query_part:
        for agg_details_as_list in query_part["aggregation"]:
            _replace_field_info_refs(
                field_info=agg_details_as_list,
                table_equivalencies=table_equivalencies,
            )
            # for agg_detail_item in agg_details_as_list:
            # if isinstance(agg_detail_item, list):
            #     if agg_detail_item[0] == "field":
            #         field_info = agg_detail_item
            #         # reference to a table's column. Replace it.
            #         old_field_id = field_info[1]
            #         if isinstance(old_field_id, int):
            #             new_field_id = find_field_destination(
            #                 old_field_id=old_field_id,
            #                 column_references=column_references,
            #                 table_src2dst=table_src2dst,
            #             )
            #             # awesomeness!
            #             field_info[1] = new_field_id

    if "expressions" in query_part:
        assert isinstance(query_part["expressions"], dict)
        for key, expr_as_list in query_part["expressions"].items():
            for field_info in expr_as_list:
                if isinstance(field_info, list):
                    _replace_field_info_refs(
                        field_info,
                        table_equivalencies=table_equivalencies,
                    )
                    # if field_info[0] == "field":
                    #     # reference to a table's column. Replace it.
                    #     old_field_id = field_info[1]
                    #     if isinstance(old_field_id, int):
                    #         new_field_id = find_field_destination(
                    #             old_field_id=old_field_id,
                    #             column_references=column_references,
                    #             table_src2dst=table_src2dst,
                    #         )
                    #         # awesomeness!
                    #         field_info[1] = new_field_id
    # breakout
    if "breakout" in query_part:
        for brk in query_part["breakout"]:
            if brk[0] == "field":
                # reference to a table's column. Replace it.
                old_field_id = brk[1]
                if isinstance(old_field_id, int):
                    new_field_id = table_equivalencies.find_field_destination(
                        old_field_id=old_field_id
                    )
                    # awesomeness!
                    brk[1] = new_field_id
    if "order-by" in query_part:
        for ob in query_part["order-by"]:
            # reference to a table's column. Replace it.
            desc = ob[1][0]
            old_field_id = ob[1][1]
            if isinstance(old_field_id, int) and (
                desc != "aggregation"
            ):  # todo: this ok?
                new_field_id = table_equivalencies.find_field_destination(
                    old_field_id=old_field_id
                )
                # awesomeness!
                ob[1][1] = new_field_id
    return query_part
