from typing import Optional


def copy_card(
    self,
    source_card_name=None,
    source_card_id=None,
    source_collection_name=None,
    source_collection_id=None,
    destination_card_name=None,
    destination_collection_name=None,
    destination_collection_id=None,
    postfix="",
    verbose=False,
):
    """
    Copy the card with the given name/id to the given destination collection.

    Keyword arguments:
    source_card_name -- name of the card to copy (default None)
    source_card_id -- id of the card to copy (default None)
    source_collection_name -- name of the collection the source card is located in (default None)
    source_collection_id -- id of the collection the source card is located in (default None)
    destination_card_name -- name used for the card in destination (default None).
                                                        If None, it will use the name of the source card + postfix.
    destination_collection_name -- name of the collection to copy the card to (default None)
    destination_collection_id -- id of the collection to copy the card to (default None)
    postfix -- if destination_card_name is None, adds this string to the end of source_card_name
                            to make destination_card_name
    """
    ### Making sure we have the data that we need
    if not source_card_id:
        if not source_card_name:
            raise ValueError(
                "Either the name or id of the source card must be provided."
            )
        else:
            source_card_id = self.get_item_id(
                item_type="card",
                item_name=source_card_name,
                collection_id=source_collection_id,
                collection_name=source_collection_name,
            )

    if not destination_collection_id:
        if not destination_collection_name:
            raise ValueError(
                "Either the name or id of the destination collection must be provided."
            )
        else:
            destination_collection_id = self.get_item_id(
                "collection", destination_collection_name
            )

    if not destination_card_name:
        if not source_card_name:
            source_card_name = self.get_item_name(
                item_type="card", item_id=source_card_id
            )
        destination_card_name = source_card_name + postfix

    # Get the source card info
    source_card = self.get("/api/card/{}".format(source_card_id))

    # Update the name and collection_id
    card_json = source_card
    card_json["collection_id"] = destination_collection_id
    card_json["name"] = destination_card_name

    # Fix the issue #10
    if card_json.get("description") == "":
        card_json["description"] = None

    # Save as a new card
    res = self.create_card(custom_json=card_json, verbose=verbose, return_card=True)

    # Return the id of the created card
    return res["id"]


def copy_pulse(
    self,
    source_pulse_name=None,
    source_pulse_id=None,
    source_collection_name=None,
    source_collection_id=None,
    destination_pulse_name=None,
    destination_collection_id=None,
    destination_collection_name=None,
    postfix="",
):
    """
    Copy the pulse with the given name/id to the given destination collection.

    Keyword arguments:
    source_pulse_name -- name of the pulse to copy (default None)
    source_pulse_id -- id of the pulse to copy (default None)
    source_collection_name -- name of the collection the source card is located in (default None)
    source_collection_id -- id of the collection the source card is located in (default None)
    destination_pulse_name -- name used for the pulse in destination (default None).
                                                        If None, it will use the name of the source pulse + postfix.
    destination_collection_name -- name of the collection to copy the pulse to (default None)
    destination_collection_id -- id of the collection to copy the pulse to (default None)
    postfix -- if destination_pulse_name is None, adds this string to the end of source_pulse_name
                            to make destination_pulse_name
    """
    ### Making sure we have the data that we need
    if not source_pulse_id:
        if not source_pulse_name:
            raise ValueError(
                "Either the name or id of the source pulse must be provided."
            )
        else:
            source_pulse_id = self.get_item_id(
                item_type="pulse",
                item_name=source_pulse_name,
                collection_id=source_collection_id,
                collection_name=source_collection_name,
            )

    if not destination_collection_id:
        if not destination_collection_name:
            raise ValueError(
                "Either the name or id of the destination collection must be provided."
            )
        else:
            destination_collection_id = self.get_item_id(
                "collection", destination_collection_name
            )

    if not destination_pulse_name:
        if not source_pulse_name:
            source_pulse_name = self.get_item_name(
                item_type="pulse", item_id=source_pulse_id
            )
        destination_pulse_name = source_pulse_name + postfix

    # Get the source pulse info
    source_pulse = self.get("/api/pulse/{}".format(source_pulse_id))

    # Updat the name and collection_id
    pulse_json = source_pulse
    pulse_json["collection_id"] = destination_collection_id
    pulse_json["name"] = destination_pulse_name

    # Save as a new pulse
    self.post("/api/pulse", json=pulse_json)


def copy_dashboard(
    self,
    source_dashboard_name=None,
    source_dashboard_id=None,
    source_collection_name=None,
    source_collection_id=None,
    destination_dashboard_name=None,
    destination_collection_name=None,
    destination_collection_id=None,
    postfix="",
    card_id_mapping: Optional[dict[int, int]] = None,
):
    """
    Copy the dashboard with the given name/id to the given destination collection.

    Keyword arguments:
    source_dashboard_name -- name of the dashboard to copy (default None)
    source_dashboard_id -- id of the dashboard to copy (default None)
    source_collection_name -- name of the collection the source dashboard is located in (default None)
    source_collection_id -- id of the collection the source dashboard is located in (default None)
    destination_dashboard_name -- name used for the dashboard in destination (default None).
                                                                If None, it will use the name of the source dashboard + postfix.
    destination_collection_name -- name of the collection to copy the dashboard to (default None)
    destination_collection_id -- id of the collection to copy the dashboard to (default None)
    deepcopy -- whether to duplicate the cards inside the dashboard (default False).
                            If True, puts the duplicated cards in a collection called "[dashboard_name]'s cards"
                            in the same path as the duplicated dashboard.
    postfix -- if destination_dashboard_name is None, adds this string to the end of source_dashboard_name
                            to make destination_dashboard_name
    card_id_mapping -- Optionally, a mapping for cards: old_id -> new_id for the dashboard to update itself.
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

    if not destination_collection_id:
        if not destination_collection_name:
            raise ValueError(
                "Either the name or id of the destination collection must be provided."
            )
        else:
            destination_collection_id = self.get_item_id(
                "collection", destination_collection_name
            )

    if not destination_dashboard_name:
        if not source_dashboard_name:
            source_dashboard_name = self.get_item_name(
                item_type="dashboard", item_id=source_dashboard_id
            )
        destination_dashboard_name = source_dashboard_name + postfix

    # shallow-copy
    shallow_copy_json = {
        "collection_id": destination_collection_id,
        "name": destination_dashboard_name,
    }
    shallow_dashboard = self.post(
        "/api/dashboard/{}/copy".format(source_dashboard_id), json=shallow_copy_json
    )
    dup_dashboard_id = shallow_dashboard["id"]

    # do we need to re-map?
    if card_id_mapping is not None:
        dup_dashboard = self.get("/api/dashboard/{}".format(dup_dashboard_id))
        for card in dup_dashboard["dashcards"]:
            # ignore text boxes. These get copied in the shallow-copy stage.
            if card["card_id"] is None:
                continue
            # replace values
            # todo: should we change update date/creation date too...?
            try:
                new_card_id = card_id_mapping[card["card_id"]]
            except KeyError as ke:
                raise KeyError(
                    f"Card {card['card_id']} is referenced in dashboard but we can't find the card itself."
                ) from ke
            card["card_id"] = new_card_id
            card["card"]["id"] = new_card_id
            # we need not to hit any existing id... that's why '100 *'.
            # todo: Can we do anything better?
            card["id"] = 100 * card["id"] + 1
        assert self.put(f"/api/dashboard/{dup_dashboard_id}", json=dup_dashboard) == 200

    return dup_dashboard_id


def copy_collection(
    self,
    source_collection_name=None,
    source_collection_id=None,
    destination_collection_name=None,
    destination_parent_collection_name=None,
    destination_parent_collection_id=None,
    deepcopy_dashboards=False,
    postfix="",
    child_items_postfix="",
    verbose=False,
) -> dict[str, dict[int, int]]:
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
    deepcopy_dashboards -- whether to duplicate the cards inside the dashboards (default False).
                                                    If True, puts the duplicated cards in a collection called "[dashboard_name]'s duplicated cards"
                                                    in the same path as the duplicated dashboard.
    postfix -- if destination_collection_name is None, adds this string to the end of source_collection_name to make destination_collection_name.
    child_items_postfix -- this string is added to the end of the child items' names, when saving them in the destination (default '').
    verbose -- prints extra information (default False)

    :return (eg)
        transf: dict[str, dict[int, int]] = {
        'cards': {
            764: 876,
            22: 33
        },
        'dashboard': {
            1: 11
        }
    }

    """
    # making sure we have the data that we need
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

    # we'll return a trace of all transformations, in format 'src:dst'
    transf: dict[str, dict[int, int]] = dict()

    # create a collection in the destination to hold the contents of the source collection
    res = self.create_collection(
        destination_collection_name,
        parent_collection_id=destination_parent_collection_id,
        parent_collection_name=destination_parent_collection_name,
        return_results=True,
    )
    if not res:
        raise ConnectionRefusedError(
            "Current user does not have permissions to create destination collection."
        )
    destination_collection_id = res["id"]

    # get the items to copy
    items = self.get("/api/collection/{}/items".format(source_collection_id))
    if (
        type(items) == dict
    ):  # in Metabase version *.40.0 the format of the returned result for this endpoint changed
        items = items["data"]

    # copy the items of the source collection to the new collection
    # first thing we want to do is copy the cards:
    card_id_mapping = {}
    if deepcopy_dashboards:
        card_items = [c for c in items if c["model"] == "card"]
        for card in card_items:
            card_id = card["id"]
            card_name = card["name"]
            destination_card_name = card_name + child_items_postfix
            self.verbose_print(verbose, 'Copying the card "{}" ...'.format(card_name))
            dup_card_id = self.copy_card(
                source_card_id=card_id,
                destination_collection_id=destination_collection_id,
                destination_card_name=destination_card_name,
            )
            card_id_mapping[card_id] = dup_card_id
        transf["cards"] = card_id_mapping
    # next we want to copy all internal collections (as they might contain cards too)
    collection_items = [c for c in items if c["model"] == "collection"]
    for collection in collection_items:
        collection_id = collection["id"]
        collection_name = collection["name"]
        # destination_collection_name = collection_name + child_items_postfix
        self.verbose_print(
            verbose, 'Copying the collection "{}" ...'.format(collection_name)
        )
        int_transf = self.copy_collection(
            source_collection_id=collection_id,
            destination_parent_collection_id=destination_collection_id,
            child_items_postfix=child_items_postfix,
            deepcopy_dashboards=deepcopy_dashboards,
            verbose=verbose,
        )
        # updates the transformations
        for k in set(transf.keys()).union(int_transf.keys()):
            transf[k] = transf.get(k, {}) | int_transf.get(k, {})
    # let's now create all other items
    for item in items:
        if item["model"] == "dashboard":  # copy a dashboard
            dashboard_id = item["id"]
            dashboard_name = item["name"]
            destination_dashboard_name = dashboard_name + child_items_postfix
            self.verbose_print(
                verbose, 'Copying the dashboard "{}" ...'.format(dashboard_name)
            )
            self.copy_dashboard(
                source_dashboard_id=dashboard_id,
                destination_collection_id=destination_collection_id,
                destination_dashboard_name=destination_dashboard_name,
                card_id_mapping=transf["cards"] if deepcopy_dashboards else None,
            )
        # copy a pulse
        elif item["model"] == "pulse":
            pulse_id = item["id"]
            pulse_name = item["name"]
            destination_pulse_name = pulse_name + child_items_postfix
            self.verbose_print(verbose, 'Copying the pulse "{}" ...'.format(pulse_name))
            self.copy_pulse(
                source_pulse_id=pulse_id,
                destination_collection_id=destination_collection_id,
                destination_pulse_name=destination_pulse_name,
            )
        elif (item["model"] == "card") or (item["model"] == "collection"):
            # all good, we already copied it! (see just before this loop)
            continue
        else:
            raise ValueError(
                f"We are not copying objects of type '{item['model']}'; specifically the one named '{item['name']}'!!!"
            )
    return transf
