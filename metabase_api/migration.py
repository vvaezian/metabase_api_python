from copy import deepcopy
from typing import Optional

from metabase_api import Metabase_API

import logging

_logger = logging.getLogger(__name__)


class ColumnReferences:
    """Keeps mapping between column id and name for a specified table."""

    def __init__(self, table_id: int, mapping: dict[str, int]):
        """mapping keeps id:name."""
        self.table_id = table_id
        self.mapping = mapping
        self.inv_mapping: dict[int, str] = {
            column_name: column_id for (column_id, column_name) in self.mapping.items()
        }

    @classmethod
    def from_metabase(
        cls, metabase_api: Metabase_API, table_id: int
    ) -> "ColumnReferences":
        dst_table_fields = metabase_api.get_columns_name_id(table_id=table_id)
        return ColumnReferences(table_id=table_id, mapping=dst_table_fields)

    def get_column_name(self, column_id: int) -> str:
        try:
            return self.inv_mapping[column_id]
        except KeyError as ke:
            raise ValueError(
                f"column with id {column_id} does not exist in table {self.table_id}"
            ) from ke

    def get_column_id(self, column_name: str) -> int:
        try:
            return self.mapping[column_name]
        except KeyError as ke:
            raise ValueError(
                f"column with name '{column_name}' does not exist in table {self.table_id}"
            ) from ke


def migrate_collection(
    metabase_api: Metabase_API,
    source_collection_id: int,
    db_target: int,
    parent_collection_id: int,
    destination_collection_name: str,
    table_src2dst: Optional[dict[int, int]] = None,
    new_dashboard_name: Optional[str] = None,
):
    # references to columns are organized as follows:
    # * key 'src' contains all source table
    # * key 'dst' contains all destination tables
    # * inside of each key we find another dictionary, with key the table id, and value the column references.
    column_references: dict[str, dict[int, ColumnReferences]] = dict()
    column_references["src"] = dict()
    column_references["dst"] = dict()
    for table_id in table_src2dst.keys():
        column_references["src"][table_id] = ColumnReferences.from_metabase(
            metabase_api=metabase_api, table_id=table_id
        )
    for table_id in table_src2dst.values():
        column_references["dst"][table_id] = ColumnReferences.from_metabase(
            metabase_api=metabase_api, table_id=table_id
        )

    source_collection_name = metabase_api.get_item_name(
        item_type="collection", item_id=source_collection_id
    )
    print(f"source_collection_name = '{source_collection_name}'")

    # let's copy the collection inside a (manually chosen) parent collect
    parent_collection_name = metabase_api.get_item_name(
        item_type="collection", item_id=parent_collection_id
    )
    print(
        f"parent collection for target=id:{parent_collection_id}, name: '{parent_collection_name}'"
    )
    # if the destination collection already exists, fail
    try:
        _ = metabase_api.get_item_id(
            item_type="collection",
            item_name=destination_collection_name,
            collection_name=destination_collection_name,
        )
        raise RuntimeError(f"Collection '{destination_collection_name}' exists")
    except ValueError as ve:
        pass
    # all good
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
    # visit all cards
    items = metabase_api.get("/api/collection/{}/items".format(dst_collection_id))
    # in Metabase version *.40.0 the format of the returned result for this endpoint changed
    if type(items) == dict:
        items = items["data"]

    for item in items:
        if item["model"] == "card":
            card_id = item["id"]
            _logger.info(f"Visiting card id '{card_id}'")
            source_card = metabase_api.get(f"/api/card/{card_id}")
            # update db and table id
            card_json = source_card
            # db
            card_json["database_id"] = db_target
            card_json["dataset_query"]["database"] = db_target
            # table
            if table_src2dst is not None:
                table_id = card_json["table_id"]
                try:
                    card_json["table_id"] = table_src2dst[table_id]
                except KeyError as ke:
                    msg = f"[re-writing references on card '{card_id}']"
                    msg += f"Table '{table_id}' is referenced at source, but no replacement is specified."
                    raise ValueError(msg)
                # and now I have to replace the fields' references to this table
                src_table_fields = column_references["src"][table_id]
                dst_table_fields = column_references["dst"][table_src2dst[table_id]]
                # change result metadata
                if ("result_metadata" not in card_json) or (
                    card_json["result_metadata"] is None
                ):
                    _logger.debug(f"[card: {card_id}] There is no 'result_metadata'")
                else:
                    for md in card_json["result_metadata"]:
                        if ("field_ref" in md) and (md["field_ref"][0] == "field"):
                            old_field_id = md["field_ref"][1]
                            if isinstance(old_field_id, int):
                                new_field_id = find_field_destination(
                                    old_field_id,
                                    column_references=column_references,
                                    table_src2dst=table_src2dst,
                                )
                                # awesomeness!
                                md["field_ref"][1] = new_field_id
                                md["id"] = new_field_id
            # change query
            query_part = card_json["dataset_query"]["query"]
            if "source-table" in query_part:
                update_query_part(
                    card_id=card_id,
                    query_part=query_part,
                    column_references=column_references,
                    cards_src2dst=transformations["cards"],
                    table_src2dst=table_src2dst,
                )
            handle_card(
                card_json,
                column_references=column_references,
                table_src2dst=table_src2dst,
                transformations=transformations,
            )
            # and go!
            assert (
                metabase_api.put("/api/card/{}".format(card_id), json=card_json) == 200
            )
    for item in items:
        if item["model"] == "dashboard":
            dashboard_id = item["id"]
            _logger.info(f"Migrating dashboard {dashboard_id}...")
            dash = metabase_api.get(f"/api/dashboard/{dashboard_id}")
            # param values
            param_values = dash["param_values"]
            for field_id_as_str, field_info in deepcopy(dash["param_values"]).items():
                field_id = int(field_id_as_str)
                new_field_id = find_field_destination(
                    old_field_id=field_id,
                    column_references=column_references,
                    table_src2dst=table_src2dst,
                )
                new_field_id_as_str = str(new_field_id)
                param_values[new_field_id_as_str] = param_values.pop(field_id_as_str)
                param_values[new_field_id_as_str]["field_id"] = new_field_id
            # param fields
            old_param_fields = deepcopy(dash["param_fields"])
            for field_id_as_str, field_info in old_param_fields.items():
                try:
                    field_id = int(field_id_as_str)
                    src_table = field_info["table_id"]
                    field_name = column_references["src"][src_table].get_column_name(
                        field_id
                    )
                    new_field_id = column_references["dst"][
                        table_src2dst[src_table]
                    ].get_column_id(field_name)
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
                    ] = table_src2dst[src_table]
                except ValueError as ve:
                    # apparently one of the param fields is not an int...?
                    pass
            for card_json in dash["dashcards"]:
                handle_card(
                    card_json,
                    column_references=column_references,
                    table_src2dst=table_src2dst,
                    transformations=transformations,
                )
            # change name, tag it, and go!
            if dash["description"] is None:
                dash["description"] = ""
            dash["description"] = dash["description"] + " (migrated by API)"
            dash["name"] = (
                new_dashboard_name if new_dashboard_name is not None else dash["name"]
            )
            r = metabase_api.put("/api/dashboard/{}".format(dashboard_id), json=dash)
            assert (
                r == 200
            ), f"Problems updating dashboard '{dashboard_id}'; code {r}"  # sanity check


def handle_card(
    card_json,
    column_references: dict[str, dict[int, ColumnReferences]],
    table_src2dst: dict[int, int],
    transformations,
):
    # mappings to filters
    for mapping in card_json["parameter_mappings"]:
        mapping["card_id"] = transformations["cards"][mapping["card_id"]]
        if "target" in mapping:
            t = mapping["target"]
            if (t[0] == "dimension") and (t[1][0] == "field"):
                t[1][1] = find_field_destination(
                    old_field_id=t[1][1],
                    column_references=column_references,
                    table_src2dst=table_src2dst,
                )
    if "visualization_settings" in card_json:
        update_viz_settings(
            viz_settings=card_json["visualization_settings"],
            column_references=column_references,
            table_src2dst=table_src2dst,
            transformations=transformations,
        )
    # # card itself
    # if ("card" in card_json) and ("visualization_settings" in card_json["card"]):
    #     update_viz_settings(
    #         viz_settings=card_json["card"]["visualization_settings"],
    #         column_references=column_references,
    #         table_src2dst=table_src2dst,
    #         transformations=transformations,
    #     )


def update_viz_settings(
    viz_settings: dict,
    column_references: dict[str, dict[int, ColumnReferences]],
    table_src2dst: dict[int, int],
    transformations,
):
    if "table.columns" in viz_settings:
        for table_column in viz_settings["table.columns"]:
            update_table_cols_info(
                table_column,
                column_references=column_references,
                table_src2dst=table_src2dst,
            )
    if "column_settings" in viz_settings:
        # first, let's change keys (if needed)
        for k in deepcopy(viz_settings["column_settings"]).keys():
            # continue
            l = eval(k.replace("null", "None"))
            if l[0] == "ref":
                field_info = l[1]
                if field_info[0] == "field":
                    field_info[1] = find_field_destination(
                        field_info[1],
                        column_references=column_references,
                        table_src2dst=table_src2dst,
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
                    column_references=column_references,
                    table_src2dst=table_src2dst,
                    transformations=transformations,
                )
    if "click_behavior" in viz_settings:
        click_behavior = viz_settings["click_behavior"]
        handle_click_behavior(
            click_behavior=click_behavior,
            column_references=column_references,
            table_src2dst=table_src2dst,
            transformations=transformations,
        )


def handle_click_behavior(
    click_behavior: dict,
    column_references: dict[str, dict[int, ColumnReferences]],
    table_src2dst: dict[int, int],
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
                        field_info[1] = find_field_destination(
                            old_field_id=field_info[1],
                            column_references=column_references,
                            table_src2dst=table_src2dst,
                        )
                        map_target["id"] = str(map_target["dimension"])
                        old_id = mapping["id"]
                        mapping["id"] = map_target["id"]
                        click_behavior["parameterMapping"].pop(old_id)
                        click_behavior["parameterMapping"][mapping["id"]] = mapping


def update_table_cols_info(
    table_column: dict,
    column_references: dict[str, dict[int, ColumnReferences]],
    table_src2dst: dict[int, int],
) -> dict:
    field_ref = table_column["fieldRef"]
    if field_ref[0] == "field":
        old_field_id = field_ref[1]
        new_field_id = find_field_destination(
            old_field_id=old_field_id,
            column_references=column_references,
            table_src2dst=table_src2dst,
        )
        field_ref[1] = new_field_id
    return table_column


def update_query_part(
    card_id: int,
    query_part: dict,  # todo: be more specific!
    column_references: dict[str, dict[int, ColumnReferences]],
    cards_src2dst: dict[int, int],  # transformations['cards']
    table_src2dst: Optional[dict[int, int]] = None,
) -> dict:  # todo: be more specific!
    """change query."""

    # table
    try:
        src_table_in_query = query_part["source-table"]
    except Exception as e:
        raise e
    if isinstance(src_table_in_query, int):
        if table_src2dst is not None:
            # if the source is an int => it MUST be the id of a table
            # (and so its correspondence must be found in the input)
            try:
                query_part["source-table"] = table_src2dst[src_table_in_query]
            except KeyError as ke:
                msg = f"[re-writing references on card '{card_id}']"
                msg += f"Table '{src_table_in_query}' is referenced at source, but no replacement is specified."
                raise ValueError(msg)
            # # and now I have to replace the fields' references to this table
            # src_table_fields = column_references["src"][src_table_in_query]
            # dst_table_fields = column_references["dst"][
            #     table_src2dst[src_table_in_query]
            # ]
    elif str(src_table_in_query).startswith("card"):
        # it's reference a card. Which one?
        ref_card_id = int(src_table_in_query.split("__")[1])
        try:
            query_part["source-table"] = f"card__{cards_src2dst[ref_card_id]}"
        except KeyError as ke:
            raise KeyError(
                f"Card {ref_card_id} is referenced in dashboard but we can't find the card itself."
            ) from ke
    else:
        raise ValueError(f"I don't know what this reference is: {src_table_in_query}")
    #
    if "filter" in query_part:
        field_info = query_part["filter"][1]
        if field_info[0] == "field":
            # reference to a table's column. Replace it.
            old_field_id = field_info[1]
            new_field_id = find_field_destination(
                old_field_id=old_field_id,
                column_references=column_references,
                table_src2dst=table_src2dst,
            )
            # awesomeness!
            field_info[1] = new_field_id
    # aggregation or filter
    for section_name in ["aggregation"]:
        if section_name in query_part:
            for agg in query_part[section_name]:
                if len(agg) > 1:
                    field_info = agg[1]
                    if field_info[0] == "field":
                        # reference to a table's column. Replace it.
                        old_field_id = field_info[1]
                        if isinstance(old_field_id, int):
                            new_field_id = find_field_destination(
                                old_field_id=old_field_id,
                                column_references=column_references,
                                table_src2dst=table_src2dst,
                            )
                            # awesomeness!
                            field_info[1] = new_field_id
    # breakout
    if "breakout" in query_part:
        for brk in query_part["breakout"]:
            if brk[0] == "field":
                # reference to a table's column. Replace it.
                old_field_id = brk[1]
                new_field_id = find_field_destination(
                    old_field_id=old_field_id,
                    column_references=column_references,
                    table_src2dst=table_src2dst,
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
                new_field_id = find_field_destination(
                    old_field_id=old_field_id,
                    column_references=column_references,
                    table_src2dst=table_src2dst,
                )
                # awesomeness!
                ob[1][1] = new_field_id
    return query_part


def find_field_destination(
    old_field_id: int,
    column_references: dict[str, dict[int, ColumnReferences]],
    table_src2dst: dict[int, int],
) -> int:
    # I am not sure to which table; I just know it's a _source_ table;
    # let's then search in ALL of them
    all_src_table_fields = column_references["src"]
    for src_table_id, src_table_fields in all_src_table_fields.items():
        dst_table_id = table_src2dst[src_table_id]
        dst_table_fields = column_references["dst"][dst_table_id]
        try:
            field_name = src_table_fields.get_column_name(old_field_id)
            # ok. Now let's go to the destination table
            return dst_table_fields.get_column_id(field_name)
        except ValueError as ke:
            # it wasn't in this table...
            continue
    # if I got here it's because I couldn't find the field anywhere!
    raise ValueError(f"Field '{old_field_id}' does not appear in any source table.")
