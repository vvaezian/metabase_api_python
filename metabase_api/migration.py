from typing import Optional

from metabase_api import Metabase_API


def migrate_collection(
    metabase_api: Metabase_API,
    source_collection_id: int,
    db_target: int,
    PARENT_COLLECTION_ID: int,
    destination_collection_name: str,
    table_src2dst: Optional[dict[int, int]] = None,
):
    #

    fail_on_exist = True  # if True, if the collection target exists, it fails. Otherwise it just gives a message.
    deep_copy = True  # True or False

    source_collection_name = metabase_api.get_item_name(
        item_type="collection", item_id=source_collection_id
    )
    print(f"source_collection_name = '{source_collection_name}'")

    # let's copy the collection inside a (manually chosen) parent collect
    parent_collection_name = metabase_api.get_item_name(
        item_type="collection", item_id=PARENT_COLLECTION_ID
    )
    print(
        f"parent collection for target=id:{PARENT_COLLECTION_ID}, name: '{parent_collection_name}'"
    )

    try:
        _ = metabase_api.get_item_id(
            item_type="collection",
            item_name=destination_collection_name,
            collection_name=destination_collection_name,
        )
        if fail_on_exist:
            raise RuntimeError(f"Collection '{destination_collection_name}' exists")
        else:
            print(
                f"'{source_collection_id}' was already duplicated as '{destination_collection_name}'. All good."
            )
    except ValueError as ve:
        # all good
        transformations = metabase_api.copy_collection(
            source_collection_id=source_collection_id,
            destination_parent_collection_id=PARENT_COLLECTION_ID,
            destination_collection_name=destination_collection_name,
            deepcopy_dashboards=deep_copy,  # this NEEDS to be set to True!
        )
        print(f"'{source_collection_id}' duplicated!")

    if deep_copy:
        dst_collection_id = metabase_api.get_item_id(
            item_type="collection",
            item_name=destination_collection_name,
            collection_name=destination_collection_name,
        )

        # visit all cards
        items = metabase_api.get("/api/collection/{}/items".format(dst_collection_id))
        if (
            type(items) == dict
        ):  # in Metabase version *.40.0 the format of the returned result for this endpoint changed
            items = items["data"]

        for item in items:
            if item["model"] == "card":
                card_id = item["id"]
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
                src_table_in_query = card_json["dataset_query"]["query"]["source-table"]
                if isinstance(src_table_in_query, int):
                    if table_src2dst is not None:
                        # if the source is an int => it MUST be the id of a table
                        # (and so its correspondence must be found in the input)
                        try:
                            card_json["dataset_query"]["query"][
                                "source-table"
                            ] = table_src2dst[src_table_in_query]
                        except KeyError as ke:
                            msg = f"[re-writing references on card '{card_id}']"
                            msg += f"Table '{src_table_in_query}' is referenced at source, but no replacement is specified."
                            raise ValueError(msg)
                elif str(src_table_in_query).startswith("card"):
                    # it's reference a card. Which one?
                    ref_card_id = int(src_table_in_query.split("__")[1])
                    card_json["dataset_query"]["query"][
                        "source-table"
                    ] = f"card__{transformations['cards'][ref_card_id]}"
                else:
                    raise ValueError(
                        f"I don't know what this reference is: {src_table_in_query}"
                    )
                # and go!
                assert (
                    metabase_api.put("/api/card/{}".format(card_id), json=card_json)
                    == 200
                )
        for item in items:
            if item["model"] == "dashboard":
                dashboard_id = item["id"]
                dash = metabase_api.get(f"/api/dashboard/{dashboard_id}")
                print(dashboard_id)
                for card_json in dash["dashcards"]:
                    # mappings to filters
                    for mapping in card_json["parameter_mappings"]:
                        mapping["card_id"] = transformations["cards"][
                            mapping["card_id"]
                        ]
                    # click behavior
                    if "click_behavior" in card_json["visualization_settings"]:
                        if (
                            "targetId"
                            in card_json["visualization_settings"]["click_behavior"]
                        ):
                            old_targetid = card_json["visualization_settings"][
                                "click_behavior"
                            ]["targetId"]
                            card_json["visualization_settings"]["click_behavior"][
                                "targetId"
                            ] = transformations["cards"][old_targetid]
                        else:
                            raise ValueError(f"no target id")
                # and go!
                assert (
                    metabase_api.put(
                        "/api/dashboard/{}".format(dashboard_id), json=dash
                    )
                    == 200
                )
    print("all done!")
