import re


def clone_collection_new_database(
    self,
    source_collection_name=None,
    source_collection_id=None,
    destination_collection_name=None,
    destination_parent_collection_name=None,
    destination_parent_collection_id=None,
    target_database_name=None,
    target_database_id=None,
    cloned_card_mapping={},
    postfix="- Duplicate",
):
    """
    Copy the collection with the given name/id into the given destination parent collection.

    Keyword arguments:
    source_collection_name -- name of the collection to copy (default None)
    source_collection_id -- id of the collection to copy (default None)
    destination_collection_name -- the name to be used for the collection in the destination (default None).
                                                                    If None, it will use the name of the source collection + postfix.
    destination_parent_collection_name -- name of the destination parent collection (default None).
                                                                                This is the collection that would have the copied collection as a child.
                                                                                use 'Root' for the root collection.
    destination_parent_collection_id -- id of the destination parent collection (default None).
                                                                            This is the collection that would have the copied collection as a child.
    target_database_name -- name of the database to target on cloned cards (default None)
    target_database_id -- id of the database to target on cloned cards (default None)
    cloned_card_mapping -- dict of all the cloned cards (default {})
    postfix -- if destination_collection_name is None, adds this string to the end of source_collection_name to make destination_collection_name.
    """
    ### making sure we have the data that we need
    if not source_collection_id:
        if not source_collection_name:
            raise ValueError(
                "Either the name or id of the source collection must be provided."
            )
        else:
            source_collection_id = self.get_item_id(
                "collection", source_collection_name
            )

    if not destination_parent_collection_id:
        if not destination_parent_collection_name:
            raise ValueError(
                "Either the name or id of the destination parent collection must be provided."
            )
        else:
            destination_parent_collection_id = (
                self.get_item_id("collection", destination_parent_collection_name)
                if destination_parent_collection_name != "Root"
                else None
            )

    if not destination_collection_name:
        if not source_collection_name:
            source_collection_name = self.get_item_name(
                item_type="collection", item_id=source_collection_id
            )
        destination_collection_name = source_collection_name + postfix

    if not target_database_id:
        if not target_database_name:
            raise ValueError(
                "Either the name or id of the target database must be provided."
            )
        else:
            target_database_id = self.get_item_id("database", target_database_name)

    ### create a collection in the destination to hold the contents of the source collection
    destination_collection = self.create_collection(
        destination_collection_name,
        parent_collection_id=destination_parent_collection_id,
        parent_collection_name=destination_parent_collection_name,
        return_results=True,
    )
    destination_collection_id = destination_collection["id"]

    ### get the items to copy
    items = self.get("/api/collection/{}/items".format(source_collection_id))
    if (
        type(items) == dict
    ):  # in Metabase version *.40.0 the format of the returned result for this endpoint changed
        items = items["data"]

    ### copy the items of the source collection to the new collection
    for item in items:
        ## clone a sub collection
        if item["model"] == "collection":
            collection_id = item["id"]
            collection_name = item["name"]
            destination_collection_name = collection_name
            self.clone_collection_new_database(
                source_collection_id=collection_id,
                destination_parent_collection_id=destination_collection_id,
                target_database_id=target_database_id,
                cloned_card_mapping=cloned_card_mapping,
            )

        ## clone a dashboard
        if item["model"] == "dashboard":
            dashboard_id = item["id"]
            dashboard_name = item["name"]
            destination_dashboard_name = dashboard_name
            self.clone_dashboard_new_database(
                source_dashboard_id=dashboard_id,
                destination_collection_id=destination_collection_id,
                destination_dashboard_name=destination_dashboard_name,
                target_database_id=target_database_id,
                cloned_card_mapping=cloned_card_mapping,
            )

        ## clone a card
        if item["model"] == "card":
            card_id = item["id"]
            self.clone_card_new_database(
                card_id=card_id,
                destination_collection_id=destination_collection_id,
                target_database_id=target_database_id,
                cloned_card_mapping=cloned_card_mapping,
            )


def clone_dashboard_new_database(
    self,
    source_dashboard_name=None,
    source_dashboard_id=None,
    source_collection_name=None,
    source_collection_id=None,
    destination_dashboard_name=None,
    destination_collection_name=None,
    destination_collection_id=None,
    target_database_name=None,
    target_database_id=None,
    cloned_card_mapping={},
    postfix="",
):
    """
    Create a new dashboard in the target collection and deepcopy each of its referenced cards targeting another database.

    Keyword arguments:
    source_dashboard_name -- name of the dashboard to copy (default None)
    source_dashboard_id -- id of the dashboard to copy (default None)
    source_collection_name -- name of the collection the source dashboard is located in (default None)
    source_collection_id -- id of the collection the source dashboard is located in (default None)
    destination_dashboard_name -- name used for the dashboard in destination (default None).
                                                                If None, it will use the name of the source dashboard + postfix.
    destination_collection_name -- name of the collection to copy the dashboard to (default None)
    destination_collection_id -- id of the collection to copy the dashboard to (default None)
    target_database_name -- name of the database to target on cloned cards (default None)
    target_database_id -- id of the database to target on cloned cards (default None)
    cloned_card_mapping -- dict of all the cloned cards (default {})
    postfix -- if destination_dashboard_name is None, adds this string to the end of source_card_name
                          to make destination_dashboard_name
    """

    ### making sure we have the data that we need
    if not source_dashboard_id:
        if not source_dashboard_name:
            raise ValueError(
                "Either the name or id of the source dashboard must be provided."
            )
        else:
            source_dashboard_id = self.get_item_id(
                item_type="dashboard",
                item_name=source_dashboard_name,
                collection_id=source_collection_id,
                collection_name=source_collection_name,
            )
    source_dashboard = self.get("/api/dashboard/{}".format(source_dashboard_id))

    if not destination_collection_id:
        if not destination_collection_name:
            raise ValueError(
                "Either the name or id of the destination collection must be provided."
            )
        else:
            destination_collection_id = self.get_item_id(
                "collection", destination_collection_name
            )

    if not target_database_id:
        if not target_database_name:
            raise ValueError(
                "Either the name or id of the target database must be provided."
            )
        else:
            target_database_id = self.get_item_id("database", target_database_name)

    if not destination_dashboard_name:
        if not source_dashboard_name:
            source_dashboard_name = source_dashboard["name"]
        destination_dashboard_name = source_dashboard_name + postfix

    # first do the shallow copy of the dashboard
    shallow_copy_json = {
        "collection_id": destination_collection_id,
        "name": destination_dashboard_name,
    }
    res = self.post(
        "/api/dashboard/{}/copy".format(source_dashboard_id), json=shallow_copy_json
    )
    new_dashboard_id = res["id"]

    # recursively clone existing dashboard cards updating their target database
    source_dashboard_card_ids = [
        dashcard["card_id"]
        for dashcard in source_dashboard["dashcards"]
        if dashcard["card_id"] is not None
    ]
    for card_id in source_dashboard_card_ids:
        self.clone_card_new_database(
            card_id=card_id,
            target_database_id=target_database_id,
            destination_collection_id=destination_collection_id,
            cloned_card_mapping=cloned_card_mapping,
        )

    # replace cards in the new dashboard with duplicated cards
    new_dashboard = self.get("/api/dashboard/{}".format(new_dashboard_id))
    new_dashcards = []
    for index, card in enumerate(new_dashboard["dashcards"]):
        # ignore text boxes as they get copied in the shallow-copy stage.
        if card["card_id"] is None:
            continue

        # prepare a json to be used for replacing the cards in the duplicated dashboard
        new_card_id = cloned_card_mapping[card["card_id"]]["id"]
        new_card_json = {}

        # sequential negative ids are used to inform Metabase to create new card
        new_card_json["id"] = -index - 1
        new_card_json["card_id"] = new_card_id
        for prop in [
            "visualization_settings",
            "col",
            "row",
            "size_x",
            "size_y",
            "series",
            "parameter_mappings",
        ]:
            new_card_json[prop] = card[prop]
        for item in new_card_json["parameter_mappings"]:
            item["card_id"] = new_card_id

        new_dashcards.append(new_card_json)

    # update the dashboard with new dashcards, the ones not mentionned are automatically removed
    self.put(
        "/api/dashboard/{}".format(new_dashboard_id),
        json={"dashcards": new_dashcards},
    )

    print(f"Dashboard {source_dashboard_id} has been cloned to {new_dashboard_id}!")

    return new_dashboard_id


def clone_card_new_database(
    self,
    card_id,
    target_database_name=None,
    target_database_id=None,
    destination_collection_id=None,
    cloned_card_mapping={},
):
    """
    Create a new card where the database source of the old card is changed to 'target_database_id'.
    Will also update select and join queries.
    A cloned card mapping dict is necessary to update cards used inside other cards (recursively).
    The target database needs to have the same tables and columns than the database source.

    Keyword arguments:
    card_id -- id of the card
    target_database_name -- name of the database to target on cloned cards (default None)
    target_database_id -- id of the database to target on cloned cards (default None)
    destination_collection_id -- id of the collection to clone the card to (default None)
    cloned_card_mapping -- dict of all the cloned cards (default {})
    """

    assert type(cloned_card_mapping) == dict

    # card already cloned, don't do it again
    if card_id in cloned_card_mapping:
        return cloned_card_mapping[card_id]

    # {'table_name': {'id': 453, columns: {'column_name': 2709, ...}}
    target_database_table_name_id_mapping = self.get_database_name_id(
        db_id=target_database_id, db_name=target_database_name
    )
    # get the card info
    card_info = self.get_item_info("card", card_id)

    # native questions - just need to change the target database
    if card_info["dataset_query"]["type"] == "native":
        card_info["dataset_query"]["database"] = target_database_id

    # simple/custom questions - have to change target database and each table to target new DB's table
    elif card_info["dataset_query"]["type"] == "query":
        source_database_id = card_info["dataset_query"]["database"]
        # {453: {'name': 'table_name', columns: {2709: 'column_name', ...}} TODO: cache
        source_database_table_id_name_mapping = self.get_database_name_id(
            db_id=source_database_id, column_id_name=True
        )
        # change the targeted database
        card_info["dataset_query"]["database"] = target_database_id

        query_data = card_info["dataset_query"]["query"]

        # transform main source-table & columns
        source_table_id = query_data["source-table"]
        source_table_is_card = "card__" in str(source_table_id)
        # source table is another card
        if source_table_is_card:
            source_table_card_id = int(source_table_id.split("__")[1])
            # already cloned card
            if source_table_card_id in cloned_card_mapping:
                query_data["source-table"] = (
                    f"card__{cloned_card_mapping[source_table_card_id]['id']}"
                )
            # referenced card has to be cloned
            else:
                cloned_card = self.clone_card_new_database(
                    card_id=source_table_card_id,
                    target_database_id=target_database_id,
                    target_database_name=target_database_name,
                    destination_collection_id=destination_collection_id,
                    cloned_card_mapping=cloned_card_mapping,
                )
                query_data["source-table"] = f"card__{cloned_card['id']}"

        # source table is another table
        else:
            source_table_name = source_database_table_id_name_mapping[source_table_id][
                "name"
            ]
            target_table_id = target_database_table_name_id_mapping[source_table_name][
                "id"
            ]
            query_data["source-table"] = target_table_id

            # store for future usage TODO: cache
            target_database_table_name_id_mapping[source_table_name]["columns"] = (
                self.get_columns_name_id(table_id=target_table_id)
            )
            source_database_table_id_name_mapping[source_table_id]["columns"] = (
                self.get_columns_name_id(table_id=source_table_id, column_id_name=True)
            )

        # transform breakout data
        if "breakout" in query_data:
            query_data_breakout_str = str(query_data["breakout"])

            # search for Ids, when fields are string based, don't modify them as they will match new table
            source_column_ids = re.findall("'field', (\d+)", query_data_breakout_str)
            # replace column IDs from old table with the column IDs from new table
            for source_col_id_str in source_column_ids:
                source_col_id = int(source_col_id_str)

                source_col_name = source_database_table_id_name_mapping[
                    source_table_id
                ]["columns"][source_col_id]
                target_col_id = target_database_table_name_id_mapping[
                    source_table_name
                ]["columns"][source_col_name]
                query_data_breakout_str = query_data_breakout_str.replace(
                    "['field', {}, ".format(source_col_id),
                    "['field', {}, ".format(target_col_id),
                )

            card_info["dataset_query"]["query"]["breakout"] = eval(
                query_data_breakout_str
            )

        # transform each joins
        if "joins" in query_data:
            updated_joins = []
            for join in query_data["joins"]:
                source_table_id = join["source-table"]
                source_table_name = source_database_table_id_name_mapping[
                    source_table_id
                ]["name"]
                target_table_id = target_database_table_name_id_mapping[
                    source_table_name
                ]["id"]
                join["source-table"] = target_table_id

                query_data_join_str = str(join)

                # store for future usage TODO: cache
                target_database_table_name_id_mapping[source_table_name]["columns"] = (
                    self.get_columns_name_id(table_id=target_table_id)
                )
                source_database_table_id_name_mapping[source_table_id]["columns"] = (
                    self.get_columns_name_id(
                        table_id=source_table_id, column_id_name=True
                    )
                )

                # search for Ids, when fields are string based, don't modify them as they will match new table
                source_column_ids = re.findall("'field', (\d+)", query_data_join_str)
                # replace column IDs from old table with the column IDs from new table
                for source_col_id_str in source_column_ids:
                    source_col_id = int(source_col_id_str)

                    # search for source source_table_name and source_col_name
                    # by looking for source_col_id to ensure identity
                    source_table_name = None
                    source_col_name = None
                    for (
                        table_name,
                        table_detail,
                    ) in source_database_table_id_name_mapping.items():
                        if source_col_id in table_detail["columns"]:
                            source_table_name = table_detail["name"]
                            source_col_name = table_detail["columns"][source_col_id]
                            break
                    target_col_id = target_database_table_name_id_mapping[
                        source_table_name
                    ]["columns"][source_col_name]
                    query_data_join_str = query_data_join_str.replace(
                        "['field', {}, ".format(source_col_id),
                        "['field', {}, ".format(target_col_id),
                    )

                updated_join = eval(query_data_join_str)
                updated_joins.append(updated_join)

            card_info["dataset_query"]["query"]["joins"] = updated_joins

    new_card_json = {}
    for key in ["dataset_query", "display", "visualization_settings", "name"]:
        new_card_json[key] = card_info[key]

    if destination_collection_id:
        new_card_json["collection_id"] = destination_collection_id
    else:
        new_card_json["collection_id"] = card_info["collection_id"]

    new_card = self.create_card(
        custom_json=new_card_json, verbose=True, return_card=True
    )
    cloned_card_mapping[card_id] = new_card
    new_card_id = new_card["id"]

    print(f"Card {card_id} has been cloned to {new_card_id}!")

    return new_card
