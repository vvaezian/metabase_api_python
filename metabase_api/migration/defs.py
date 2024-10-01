import logging
from copy import copy, deepcopy

from metabase_api.objects.card import Card
from metabase_api.objects.defs import (
    TraverseStack,
    ReturnValue,
    TraverseStackElement,
    CardParameters,
)

_logger = logging.getLogger(__name__)


def migration_function(
    caller_json: dict, params: CardParameters, call_stack: TraverseStack
) -> ReturnValue:
    # todo: caller_json: change the name, since this can be a json or a list
    if call_stack.empty:
        raise RuntimeError("Call stack is empty - this shouldn't happen!")
    top_of_stack = call_stack[-1]
    _logger.debug(f"[migration] on: '{top_of_stack}'")
    if top_of_stack == TraverseStackElement.CARD:
        card_json = caller_json
        if "database_id" in card_json:
            card_json["database_id"] = (
                params.db_target if card_json["database_id"] is not None else None
            )
        if "dataset_query" in card_json:
            card_json["dataset_query"]["database"] = params.db_target
        # table
        table_id = card_json.get("table_id", None)
        if table_id is not None:
            try:
                card_json["table_id"] = params.table_equivalencies[table_id].unique_id
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
                if "table_id" in md:
                    md["table_id"] = params.table_equivalencies[table_id].unique_id
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
            if "database_id" in card:
                if card["database_id"] != params.db_target:
                    card["database_id"] = params.db_target
        # mappings to filters
        for mapping in card_json.get("parameter_mappings", []):
            if "card_id" in mapping:
                mapping["card_id"] = params.transformations["cards"][mapping["card_id"]]
            if "target" in mapping:
                t = mapping["target"]
                if (t[0] == "dimension") and (t[1][0] == "field"):
                    if isinstance(t[1][1], int):  # is this a column ID?
                        t[1][1] = params.replace_column_id(column_id=t[1][1])
                    else:  # no, no column ID - then maybe column NAME?
                        _r = params.personalization_options.fields_replacements.get(
                            t[1][1], None
                        )
                        if _r is not None:
                            t[1][1] = _r
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
                ).migrate(params=params)
                query_part["source-table"] = f"card__{new_card_id}"
            else:
                raise ValueError(
                    f"I don't know what this reference is: {src_table_in_query}"
                )
        if "filter" in query_part:
            params._handle_condition_filter(filter_parts=query_part["filter"])
        if "aggregation" in query_part:
            for agg_details_as_list in query_part["aggregation"]:
                params._replace_field_info_refs(
                    field_info=agg_details_as_list,
                )
        if "expressions" in query_part:
            assert isinstance(query_part["expressions"], dict)
            for key, expr_as_list in query_part["expressions"].items():
                try:
                    params._replace_field_info_refs(expr_as_list)
                except Exception as e:
                    raise e
        # breakout
        if "breakout" in query_part:
            new_field_ids: set[int] = set()
            brk_result: list = []
            for _brk in query_part["breakout"]:
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
                else:
                    brk_result.append(brk)
            query_part["breakout"] = brk_result
        if "order-by" in query_part:
            for ob in query_part["order-by"]:
                # reference to a table's column. Replace it.
                desc = ob[1][0]
                old_field_id = ob[1][1]
                if isinstance(old_field_id, int) and (desc != "aggregation"):
                    ob[1][1] = params.replace_column_id(column_id=old_field_id)

        if "fields" in query_part:
            query_part["fields"] = params._replace_field_info_refs(query_part["fields"])
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
        return ReturnValue(new_table_columns)
    elif top_of_stack == TraverseStackElement.TABLE_COLUMN:
        table_column = caller_json
        for key, value in table_column.items():
            if key == "fieldRef":
                field_ref = value  # table_column["fieldRef"]
                if field_ref[0] == "field":
                    old_field_id = field_ref[1]
                    if isinstance(old_field_id, int):
                        field_ref[1] = params.replace_column_id(column_id=old_field_id)
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
            elif key == "name":
                if value in params.personalization_options.fields_replacements:
                    table_column[
                        key
                    ] = params.personalization_options.fields_replacements[value]
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
        if "targetId" in click_behavior:
            old_targetid = click_behavior["targetId"]
            try:
                new_targetid = params.transformations["cards"][old_targetid]
            except KeyError:
                msg = f"Target '{old_targetid}' is referenced at source, but no replacement is specified."
                _logger.error(msg)
                raise RuntimeError(msg)
            click_behavior["targetId"] = new_targetid
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
    elif top_of_stack == TraverseStackElement.GRAPH_DIMENSIONS:
        graph_dimensions = caller_json
        _l = []
        for _v in graph_dimensions:
            # do I have to replace it?
            _r = params.personalization_options.fields_replacements.get(_v, None)
            _l.append(_r if _r is not None else _v)
        return ReturnValue(_l)
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
    return ReturnValue(None)
