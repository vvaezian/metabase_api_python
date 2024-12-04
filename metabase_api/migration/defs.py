import logging
from copy import copy, deepcopy

from metabase_api.objects.card import Card
from metabase_api.objects.defs import (
    TraverseStack,
    ReturnValue,
    TraverseStackElement,
    MigrationParameters,
)

_logger = logging.getLogger(__name__)


def migration_function(
    caller_json: dict, params: MigrationParameters, call_stack: TraverseStack
) -> ReturnValue:
    # todo: caller_json: change the name, since this can be a json or a list
    if call_stack.empty:
        raise RuntimeError("Call stack is empty - this shouldn't happen!")
    top_of_stack = call_stack.top
    r = ReturnValue.empty()
    modified: bool = False
    if top_of_stack == TraverseStackElement.CARD:
        card_json = caller_json
        if "database_id" in card_json:
            card_json["database_id"] = (
                params.db_target if card_json["database_id"] is not None else None
            )
            modified = True
        if "dataset_query" in card_json:
            card_json["dataset_query"]["database"] = params.db_target
            modified = True
        # table
        table_id = card_json.get("table_id", None)
        if table_id is not None:
            try:
                card_json["table_id"] = params.table_equivalencies[table_id].unique_id
                modified = True
            except KeyError as ke:
                # mmmh... by any chance is this table_id already in target?
                # (in which case it would mean that it had already been replaced)
                if table_id not in params.table_equivalencies.dst_tables_ids:
                    msg = ""
                    # msg = f"[re-writing references on card '{card_id}']"
                    msg += f"Table '{table_id}' is referenced at source, but no replacement is specified."
                    raise ValueError(msg) from ke
            # and now I have to replace the fields' references to this table
            # these next 2 lines were not used. Commenting them as I don't understand what's up. todo: delete?
            # src_table_fields = column_references["src"][table_id]
            # dst_table_fields = column_references["dst"][table_src2dst[table_id]]
        # change result metadata
        if ("result_metadata" in card_json) and (
            card_json["result_metadata"] is not None
        ):
            for md in card_json["result_metadata"]:
                if ("field_ref" in md) and (md["field_ref"][0] == "field"):
                    old_field_id = md["field_ref"][1]
                    if isinstance(old_field_id, int):
                        new_field_id = params.replace_column_id(column_id=old_field_id)
                        md["field_ref"][1] = new_field_id
                        md["id"] = new_field_id
                        modified = True
                if "table_id" in md:
                    md["table_id"] = params.table_equivalencies[table_id].unique_id
                    modified = True
        """this is handle_card() -- it replaces self.handle_card(card_json, action=action)"""
        # card itself
        if "card" in card_json:
            card = card_json["card"]
            if "table_id" in card:
                if card["table_id"] is not None:
                    if (
                        card["table_id"]
                        not in params.table_equivalencies.dst_tables_ids
                    ):
                        card["table_id"] = params.table_equivalencies[
                            card["table_id"]
                        ].unique_id
                        modified = True
            if "database_id" in card:
                if card["database_id"] != params.db_target:
                    card["database_id"] = params.db_target
                    modified = True
        # mappings to filters
        for mapping in card_json.get("parameter_mappings", []):
            if "card_id" in mapping:
                mapping["card_id"] = params.transformations["cards"][mapping["card_id"]]
            if "target" in mapping:
                t = mapping["target"]
                if (t[0] == "dimension") and (t[1][0] == "field"):
                    if isinstance(t[1][1], int):  # is this a column ID?
                        t[1][1] = params.replace_column_id(column_id=t[1][1])
                        modified = True
                    else:  # no, no column ID - then maybe column NAME?
                        _r = params.personalization_options.fields_replacements.get(
                            t[1][1], None
                        )
                        if _r is not None:
                            t[1][1] = _r
                            modified = True
    elif top_of_stack == TraverseStackElement.VISUALIZATION_SETTINGS:
        viz_settings = caller_json
        for k, v in viz_settings.items():
            if k == "graph.dimensions":
                graph_dimensions = v
                _l = []
                for _v in graph_dimensions:
                    # do I have to replace it?
                    _r = params.personalization_options.fields_replacements.get(
                        _v, None
                    )
                    _l.append(_r if _r is not None else _v)
                    modified = True
                viz_settings["graph.dimensions"] = _l
    elif top_of_stack == TraverseStackElement.PARAMETER:
        params_dict = caller_json
        # let's update all references
        if params_dict.get("values_source_type", "nothing") == "card":
            src_config = params_dict["values_source_config"]
            src_config["card_id"] = params.transformations["cards"][
                src_config["card_id"]
            ]
            if "value_field" in src_config:
                value_field = src_config["value_field"]
                if value_field[0] == "field":
                    if isinstance(value_field[1], int):
                        value_field[
                            1
                        ] = params.table_equivalencies.column_equivalent_for(
                            column_id=value_field[1]
                        )
                        modified = True
    elif top_of_stack == TraverseStackElement.PARAM_VALUES:
        param_values = caller_json
        for field_id_as_str, field_info in deepcopy(param_values).items():
            field_id = int(field_id_as_str)
            # was it already migrated?
            if (
                params.table_equivalencies.target_table_for_column(column_id=field_id)
                is None
            ):
                new_field_id = params.replace_column_id(column_id=field_id)
                # by any chance, is this column _already_ on a target table?
                if (
                    params.table_equivalencies.target_table_for_column(
                        column_id=new_field_id
                    )
                    is None
                ):
                    # no, it's not already migrated. Carry on!
                    new_field_id_as_str = str(new_field_id)
                    param_values[new_field_id_as_str] = param_values.pop(
                        field_id_as_str
                    )
                    param_values[new_field_id_as_str]["field_id"] = new_field_id
                    param_values[new_field_id_as_str]["values"] = list()
                    modified = True
    elif top_of_stack == TraverseStackElement.PARAM_FIELDS:
        old_param_fields = caller_json
        new_ks: dict[str, str] = {}
        for field_id_as_str, field_info in old_param_fields.items():
            try:
                field_id = int(field_id_as_str)
                # if this field is _already_ on the target tables, no need to migrate it:
                field_on_target = (
                    params.table_equivalencies.target_table_for_column(
                        column_id=field_id
                    )
                    is not None
                )
                if not field_on_target:
                    src_table_id = field_info["table_id"]
                    field_name = params.table_equivalencies.get_src_table(
                        table_id=src_table_id
                    ).get_column_name(column_id=field_id)
                    dst_table_id = params.table_equivalencies[src_table_id].unique_id
                    new_field_id = params.table_equivalencies.get_dst_table(
                        dst_table_id
                    ).get_column_id(field_name)
                    # ok. Let's now change:
                    field_info["table_id"] = dst_table_id
                    field_info["id"] = new_field_id
                    # and remember to change the key of the overlaying dictionary
                    new_ks[field_id_as_str] = str(new_field_id)
            except ValueError as ve:
                raise RuntimeError(
                    "apparently one of the param fields is not an int...?"
                ) from ve
        # ok, time to replace keys:
        for old_key, new_key in new_ks.items():
            old_param_fields[new_key] = old_param_fields[old_key]
            del old_param_fields[old_key]
        modified = True
    elif top_of_stack == TraverseStackElement.QUERY_PART:
        query_part = caller_json
        # table
        if "source-table" in query_part:
            src_table_in_query = query_part["source-table"]
            if isinstance(src_table_in_query, int):
                # if the source is an int => it MUST be the id of a table
                # (and so its correspondence must be found in the input)
                try:
                    query_part["source-table"] = params.table_equivalencies[
                        src_table_in_query
                    ].unique_id
                    modified = True
                except KeyError as ke:
                    msg = ""
                    # msg = f"[re-writing references on card '{card_id}']"
                    msg += f"Table '{src_table_in_query}' is referenced at source, but no replacement is specified."
                    raise ValueError(msg) from ke
                # # and now I have to replace the fields' references to this table
                # src_table_fields = column_references["src"][src_table_in_query]
                # dst_table_fields = column_references["dst"][
                #     table_src2dst[src_table_in_query]
                # ]
            elif str(src_table_in_query).startswith("card"):
                # it's reference a card. Which one?
                # (Why: because when we find such reference,
                # this referenced card MUST be migrated before the referencees cards)
                ref_card_id = int(src_table_in_query.split("__")[1])
                try:
                    new_card_id = params.transformations["cards"][ref_card_id]
                except KeyError as ke:
                    raise KeyError(
                        f"Card {ref_card_id} is referenced in dashboard but we can't find the card itself."
                    ) from ke
                _logger.debug(f"=---- migrating referenced card '{new_card_id}'")
                Card.from_id(
                    card_id=new_card_id, metabase_api=params.metabase_api
                ).migrate(params=params, push=True)
                query_part["source-table"] = f"card__{new_card_id}"
                modified = True
            else:
                raise ValueError(
                    f"I don't know what this reference is: {src_table_in_query}"
                )
        if "filter" in query_part:
            params._handle_condition_filter(filter_parts=query_part["filter"])
            modified = True
        if "aggregation" in query_part:
            for agg_details_as_list in query_part["aggregation"]:
                params._replace_field_info_refs(
                    field_info=agg_details_as_list,
                )
                modified = True
        if "expressions" in query_part:
            assert isinstance(query_part["expressions"], dict)
            for key, expr_as_list in query_part["expressions"].items():
                try:
                    params._replace_field_info_refs(expr_as_list)
                    modified = True
                except Exception as e:
                    raise e
        # breakout
        if "breakout" in query_part:
            new_field_ids: set[int] = set()
            brk_result: list = []
            for _brk in query_part["breakout"]:
                changed = False
                brk = copy(_brk)
                if brk[0] == "field":
                    # reference to a table's column. Replace it.
                    old_field_id = brk[1]
                    if isinstance(old_field_id, int):
                        new_field_id = params.replace_column_id(column_id=old_field_id)
                        # are fields repeated, now that we have (potentially) replaced fields?
                        if new_field_id not in new_field_ids:
                            # 'else' == I already have this field!
                            brk[1] = new_field_id
                            new_field_ids.add(new_field_id)
                            brk_result.append(brk)
                            changed = True
                if not changed:
                    brk_result.append(brk)
            query_part["breakout"] = brk_result
            modified = True
        if "order-by" in query_part:
            for ob in query_part["order-by"]:
                # reference to a table's column. Replace it.
                desc = ob[1][0]
                old_field_id = ob[1][1]
                if isinstance(old_field_id, int) and (desc != "aggregation"):
                    ob[1][1] = params.replace_column_id(column_id=old_field_id)
                    modified = True
        if "fields" in query_part:
            query_part["fields"] = params._replace_field_info_refs(query_part["fields"])
            modified = True
    elif top_of_stack == TraverseStackElement.TABLE_COLUMNS:
        all_table_columns = caller_json  # it is a list
        new_table_columns: list[dict[str, str]] = []
        names_visited: set[str] = set()
        for d in all_table_columns:
            if "name" in d:
                if d["name"] not in names_visited:
                    new_table_columns.append(d)
                    names_visited.add(d["name"])
            else:
                new_table_columns.append(d)
                modified = True
        r = r.union(ReturnValue(new_table_columns))
    elif top_of_stack == TraverseStackElement.TABLE_COLUMN:
        table_column = caller_json
        for key, value in table_column.items():
            if key == "fieldRef":
                field_ref = value  # table_column["fieldRef"]
                if field_ref[0] == "field":
                    old_field_id = field_ref[1]
                    if isinstance(old_field_id, int):
                        field_ref[1] = params.replace_column_id(column_id=old_field_id)
                        modified = True
            elif key == "key":
                l = eval(value.replace("null", "None"))
                if l[0] == "ref":
                    field_info = l[1]
                    if field_info[0] == "field":
                        field_info[1] = params.replace_column_id(
                            column_id=field_info[1]
                        )
                        table_column[key] = (
                            str(l)
                            .replace("None", "null")
                            .replace("'", '"')
                            .replace(" ", "")
                        )
                        modified = True
            elif key == "name":
                if value in params.personalization_options.fields_replacements:
                    table_column[
                        key
                    ] = params.personalization_options.fields_replacements[value]
                    modified = True
            elif key == "enabled":
                _logger.debug(
                    f"WARNING [replacement] Do I have to do something with '{key}'??????? (currently = '{value}')"
                )
            else:
                _logger.debug(
                    f"WARNING [replacement] (I think not, but...) Do I have to do something with '{key}'? (currently = '{value}')"
                )
    elif top_of_stack == TraverseStackElement.CLICK_BEHAVIOR:
        click_behavior = caller_json  # it is a dictionary
        if "tabId" in click_behavior:
            old_targetid = click_behavior["tabId"]
            new_targetid: int
            try:
                new_targetid = params.transformations["tabs"][old_targetid]
            except KeyError:
                msg = f"Tab '{old_targetid}' is referenced at source, but no replacement is specified."
                _logger.error(msg)
                raise RuntimeError(msg)
            click_behavior["tabId"] = new_targetid
            modified = True
        if "targetId" in click_behavior:
            old_targetid = click_behavior["targetId"]
            new_targetid: int
            try:
                # is it a card?
                new_targetid = params.transformations["cards"][old_targetid]
            except KeyError:
                try:
                    # is it a dashboard?
                    new_targetid = params.transformations["dashboards"][old_targetid]
                except KeyError:
                    msg = f"Target '{old_targetid}' is referenced at source, "
                    msg += "but no replacement is specified (as a card nor as a dashboard)."
                    _logger.error(msg)
                    raise RuntimeError(msg)
            click_behavior["targetId"] = new_targetid
            modified = True
    elif top_of_stack == TraverseStackElement.PARAMETER_MAPPING:
        param_mapping = caller_json
        for mapping_name, mapping in deepcopy(param_mapping).items():
            # I can see fields in 'target'. # todo: are there some in 'source' too...?
            if "target" in mapping:
                map_target = mapping["target"]
                if map_target["type"] == "dimension":
                    map_target_dim = map_target["dimension"]
                    field_info = map_target_dim[1]
                    if field_info[0] == "field":
                        if isinstance(field_info[1], int):
                            field_info[1] = params.replace_column_id(
                                column_id=field_info[1]
                            )
                        map_target["id"] = str(map_target["dimension"])
                        old_id = mapping["id"]
                        mapping["id"] = map_target["id"]
                        param_mapping.pop(old_id)
                        param_mapping[mapping["id"]] = mapping
                        modified = True
                elif map_target["type"] != "parameter":
                    print(f"what do I do with '{map_target['type']}'?")
        for mapping_name, mapping in param_mapping.items():
            if "source" in mapping:
                map_src = mapping["source"]
                if map_src["type"] == "column":
                    if "id" in map_src:
                        if isinstance(map_src["id"], int):
                            map_src["id"] = params.replace_column_id(map_src["id"])
                            modified = True  # todo
                        else:
                            if (
                                map_src["id"]
                                in params.personalization_options.fields_replacements
                            ):
                                map_src[
                                    "id"
                                ] = params.personalization_options.fields_replacements[
                                    map_src["id"]
                                ]
                                modified = True
                    if "name" in map_src:
                        if (
                            map_src["name"]
                            in params.personalization_options.fields_replacements
                        ):
                            map_src[
                                "name"
                            ] = params.personalization_options.fields_replacements[
                                map_src["name"]
                            ]
                            modified = True
                # elif map_src['type'] != 'parameter':
                else:
                    print(f"what do I do with '{map_src['type']}'?")

    elif top_of_stack == TraverseStackElement.GRAPH_DIMENSIONS:
        graph_dimensions = caller_json
        _l = []
        for _v in graph_dimensions:
            # do I have to replace it?
            _r = params.personalization_options.fields_replacements.get(_v, None)
            _l.append(_r if _r is not None else _v)
            modified = True
        r = r.union(ReturnValue(_l))
    elif top_of_stack == TraverseStackElement.COLUMN_SETTINGS:
        column_settings = caller_json
        # let's change keys (if needed)
        for _k in deepcopy(column_settings).keys():
            l = eval(_k.replace("null", "None"))
            if l[0] == "ref":
                field_info = l[1]
                if field_info[0] == "field":
                    field_info[1] = params.replace_column_id(field_info[1])
                    new_k = (
                        str(l)
                        .replace("None", "null")
                        .replace("'", '"')
                        .replace(" ", "")
                    )
                    column_settings[new_k] = column_settings.pop(_k)
                    modified = True
            elif l[0] == "name":
                _old_value = l[1]
                # do I have to replace it?
                l[1] = params.personalization_options.fields_replacements.get(
                    l[1], l[1]
                )
                modified = l[1] != _old_value
                if modified:
                    new_k = (
                        str(l)
                        .replace("None", "null")
                        .replace("'", '"')
                        .replace(" ", "")
                    )
                    column_settings[new_k] = column_settings.pop(_k)
    if modified:
        _logger.debug(
            f"[migration] worked on {top_of_stack.name} (stack: {call_stack})"
        )
    return r
