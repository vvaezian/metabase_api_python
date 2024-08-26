from typing import Optional

from enum import Enum, auto


class ItemType(Enum):
    DATABASE = auto()
    TABLE = auto()
    CARD = auto()
    COLLECTION = auto()
    DASHBOARD = auto()
    PULSE = auto()
    SEGMENT = auto()

    def __str__(self) -> str:
        return self.name.lower()


def get_item_info_from_id(
    self,
    item_type: ItemType,
    item_id,
    params: Optional[dict] = None,
) -> dict:
    """

    Args:
        self:
        item_type:
        item_id:
        params:

    Returns:

    """
    """
    Return the info for the given item.
    Use 'params' for providing arguments. E.g. to include db in the result for databases, use: params={'include':'db'}
    """
    as_str = str(item_id)
    res = self.get(f"/api/{item_type}/{as_str}", params=params)
    if res:
        return res
    else:
        raise ValueError(f'There is no {as_str} with the id "{item_id}"')


def get_item_name(self, item_type: ItemType, item_id):

    res = self.get(f"/api/{str(item_type)}/{item_id}")
    if res:
        return res["name"]
    else:
        raise ValueError('There is no {} with the id "{}"'.format(item_type, item_id))


def get_item_info_from_name(
    self,
    item_type: ItemType,
    item_name: str,
    collection_id=None,
    collection_name=None,
    db_id=None,
    db_name=None,
    table_id=None,
) -> list[dict]:
    """
    Gets info for ALL items matching a name.

    Args:
        self: this module.
        item_type:
        item_name:
        collection_id:
        collection_name:
        db_id:
        db_name:
        table_id:

    Returns: a list of full info (as json) for items matching the name; if nobody matches, returns empty.

    """

    if item_type in [ItemType.CARD, ItemType.DASHBOARD, ItemType.PULSE]:
        if not collection_id:
            if not collection_name:
                # Collection name/id is not provided. Searching in all collections
                return [
                    i
                    for i in self.get(f"/api/{str(item_type)}/")
                    if i["name"] == item_name and not i["archived"]
                ]
            else:
                collection_id = (
                    self.get_item_id("collection", collection_name)
                    if collection_name != "root"
                    else None
                )
                return [
                    i
                    for i in self.get(f"/api/{str(item_type)}/")
                    if i["name"] == item_name
                    and i["collection_id"] == collection_id
                    and i["archived"] == False
                ]
        else:
            return [
                i
                for i in self.get(f"/api/{str(item_type)}/")
                if i["name"] == item_name
                and i["collection_id"] == collection_id
                and i["archived"] == False
            ]
    elif item_type == ItemType.COLLECTION:
        return [i for i in self.get("/api/collection/") if i["name"] == item_name]
    elif item_type == ItemType.DATABASE:
        res = self.get("/api/database/")
        if (
            type(res) == dict
        ):  # in Metabase version *.40.0 the format of the returned result for this endpoint changed
            res = res["data"]
        return [i for i in res if i["name"] == item_name]
    elif item_type == ItemType.TABLE:
        tables = self.get("/api/table/")

        if db_id:
            return [
                i for i in tables if i["name"] == item_name and i["db"]["id"] == db_id
            ]
        elif db_name:
            return [
                i
                for i in tables
                if i["name"] == item_name and i["db"]["name"] == db_name
            ]
        else:
            return [i for i in tables if i["name"] == item_name]
    elif item_type == ItemType.SEGMENT:
        return [
            i
            for i in self.get("/api/segment/")
            if i["name"] == item_name and (not table_id or i["table_id"] == table_id)
        ]


def get_item_id(
    self,
    item_type: ItemType,
    item_name: str,
    collection_id=None,
    collection_name=None,
    db_id=None,
    db_name=None,
    table_id=None,
):
    """Gets item id for object. Raises Exception if there are more than 1 such objects, or 0 of them."""

    all_infos = get_item_info_from_name(
        self,
        item_type=item_type,
        item_name=item_name,
        collection_id=collection_id,
        collection_name=collection_name,
        db_id=db_id,
        db_name=db_name,
        table_id=table_id,
    )
    all_ids = [i["id"] for i in all_infos]
    if len(all_ids) > 1:
        msg = f'There is more than one {item_type} with the name "{item_name}"'
        msg += (
            "Provide collection id/name to limit the search space"
            if not collection_name
            else f'in the collection "{collection_name}"'
        )
        raise ValueError(msg)
    if len(all_ids) == 0:
        msg = f'There is no {item_type} with the name "{item_name}"'
        msg += f" in the collection '{collection_name}'" if collection_name else ""
        raise ValueError(msg)
    return all_ids[0]


def get_db_id_from_table_id(self, table_id):
    tables = [i["db_id"] for i in self.get("/api/table/") if i["id"] == table_id]

    if len(tables) == 0:
        raise ValueError(
            'There is no DB containing the table with the ID "{}"'.format(table_id)
        )

    return tables[0]


def get_table_metadata(
    self, table_name=None, table_id=None, db_name=None, db_id=None, params=None
):

    if params:
        assert type(params) == dict

    if not table_id:
        if not table_name:
            raise ValueError("Either the name or id of the table needs to be provided.")
        table_id = self.get_item_id("table", table_name, db_name=db_name, db_id=db_id)

    return self.get("/api/table/{}/query_metadata".format(table_id), params=params)


def get_columns_name_id(
    self,
    db_name=None,
    table_id=None,
    db_id=None,
    column_id_name=False,
):
    """
    Return a dictionary with col_name key and col_id value, for the given table_id/table_name in the given db_id/db_name.
    If column_id_name is True, return a dictionary with col_id key and col_name value.
    """
    if not self.friendly_names_is_disabled():
        raise ValueError(
            'Please disable "Friendly Table and Field Names" from Admin Panel > Settings > General, and try again.'
        )

    if table_id:
        md = self.get_table_metadata(table_id=table_id)
        table_name = md["name"]
        table_schema = md["schema"]
    else:
        raise NotImplementedError(
            f"Can't respond without a table_id; implementation to come."
        )

    # Get db_id
    if not db_id:
        if db_name:
            db_id = self.get_item_id("database", db_name)
        else:
            if not table_id:
                table_id = self.get_item_id("table", table_name)
            db_id = self.get_db_id_from_table_id(table_id)

    # Get column names and IDs
    key, value = ("id", "name") if column_id_name else ("name", "id")
    return {
        i[key]: i[value]
        for i in self.get(f"/api/database/{db_id}/fields")
        if (i["table_name"] == table_name) and (i["schema"] == table_schema)
    }


def friendly_names_is_disabled(self):
    """
    The endpoint /api/database/:db-id/fields which is used in the function get_columns_name_id relies on the display name of fields.
    If "Friendly Table and Field Names" (in Admin Panel > Settings > General) is not disabled, it changes the display name of fields.
    So it is important to make sure this setting is disabled, before running the get_columns_name_id function.
    """
    # checking whether friendly_name is disabled required admin access.
    # So to let non-admin users also use this package we skip this step for them.
    # There is warning in the __init__ method for these users.
    if not self.is_admin:
        return True

    settings = self.get("/api/setting")
    if not isinstance(settings, list):
        return True
    friendly_name_setting = [
        i["value"] for i in settings if i["key"] == "humanization-strategy"
    ][0]
    return friendly_name_setting == "none"  # 'none' means disabled


@staticmethod
def verbose_print(verbose, msg):
    if verbose:
        print(msg)
