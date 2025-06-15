
async def get_item_info(self, item_type, item_id=None, item_name=None,
                            collection_id=None, collection_name=None,
                            params=None):
    """Async version of get_item_info"""
    assert item_type in ['database', 'table', 'card', 'collection', 'dashboard', 'pulse', 'segment']

    if params:
        assert type(params) == dict

    if not item_id:
        if not item_name:
            raise ValueError(f'Either the name or id of the {item_type} must be provided.')
        item_id = await self.get_item_id(item_type, item_name, collection_id=collection_id, collection_name=collection_name)

    res = await self.get(f"/api/{item_type}/{item_id}", params=params)
    if res:
        return res
    else:
        raise ValueError(f'There is no {item_type} with the id "{item_id}"')



async def get_item_name(self, item_type, item_id):
    """Async version of get_item_name"""
    assert item_type in ['database', 'table', 'card', 'collection', 'dashboard', 'pulse', 'segment']

    res = await self.get(f"/api/{item_type}/{item_id}")
    if res:
        return res['name']
    else:
        raise ValueError(f'There is no {item_type} with the id "{item_id}"')



async def get_item_id(self, item_type, item_name, collection_id=None, collection_name=None, db_id=None, db_name=None, table_id=None):
    """Async version of get_item_id"""
    assert item_type in ['database', 'table', 'card', 'collection', 'dashboard', 'pulse', 'segment']

    if item_type in ['card', 'dashboard', 'pulse']:
        if not collection_id:
            if not collection_name:
                # Collection name/id is not provided. Searching in all collections 
                items = await self.get(f"/api/{item_type}/")
                item_IDs = [i['id'] for i in items if i['name'] == item_name and i['archived'] == False]
            else:
                collection_id = await self.get_item_id('collection', collection_name) if collection_name != 'root' else None
                items = await self.get(f"/api/{item_type}/")
                item_IDs = [i['id'] for i in items if i['name'] == item_name 
                            and i['collection_id'] == collection_id 
                            and i['archived'] == False]
        else:
            collection_name = await self.get_item_name('collection', collection_id)
            items = await self.get(f"/api/{item_type}/")
            item_IDs = [i['id'] for i in items if i['name'] == item_name 
                        and i['collection_id'] == collection_id 
                        and i['archived'] == False]

        if len(item_IDs) > 1:
            if not collection_name:
                raise ValueError(f'There is more than one {item_type} with the name "{item_name}".\n\
                        Provide collection id/name to limit the search space')
            raise ValueError(f'There is more than one {item_type} with the name "{item_name}" in the collection "{collection_name}"')
        if len(item_IDs) == 0:
            if not collection_name:
                    raise ValueError(f'There is no {item_type} with the name "{item_name}"')
            raise ValueError(f'There is no item with the name "{item_name}" in the collection "{collection_name}"')

        return item_IDs[0]

    if item_type == 'collection':
        collections = await self.get("/api/collection/")
        collection_IDs = [i['id'] for i in collections if i['name'] == item_name]

        if len(collection_IDs) > 1:
            raise ValueError(f'There is more than one collection with the name "{item_name}"')
        if len(collection_IDs) == 0:
            raise ValueError(f'There is no collection with the name "{item_name}"')

        return collection_IDs[0]

    if item_type == 'database':
        res = await self.get("/api/database/")
        if type(res) == dict:  # in Metabase version *.40.0 the format of the returned result for this endpoint changed
            res = res['data']
        db_IDs = [i['id'] for i in res if i['name'] == item_name]

        if len(db_IDs) > 1:
            raise ValueError(f'There is more than one DB with the name "{item_name}"')
        if len(db_IDs) == 0:
            raise ValueError(f'There is no DB with the name "{item_name}"')

        return db_IDs[0]

    if item_type == 'table':
        tables = await self.get("/api/table/")

        if db_id:
            table_IDs = [i['id'] for i in tables if i['name'] == item_name and i['db']['id'] == db_id]
        elif db_name:
            table_IDs = [i['id'] for i in tables if i['name'] == item_name and i['db']['name'] == db_name]
        else:
            table_IDs = [i['id'] for i in tables if i['name'] == item_name]

        if len(table_IDs) > 1:
            raise ValueError(f'There is more than one table with the name {item_name}. Provide db id/name.')
        if len(table_IDs) == 0:
            raise ValueError(f'There is no table with the name "{item_name}" (in the provided db, if any)')

        return table_IDs[0]

    if item_type == 'segment':
        segments = await self.get("/api/segment/")
        segment_IDs = [i['id'] for i in segments if i['name'] == item_name and (not table_id or i['table_id'] == table_id)]
        
        if len(segment_IDs) > 1:
            raise ValueError(f'There is more than one segment with the name "{item_name}"')
        if len(segment_IDs) == 0:
            raise ValueError(f'There is no segment with the name "{item_name}"')

        return segment_IDs[0]


async def get_db_id_from_table_id(self, table_id):
    """Async version of get_db_id_from_table_id"""
    tables = await self.get("/api/table/")
    tables_filtered = [i['db_id'] for i in tables if i['id'] == table_id]

    if len(tables_filtered) == 0:
        raise ValueError(f'There is no DB containing the table with the ID "{table_id}"')

    return tables_filtered[0]


async def get_db_info(self, db_name=None, db_id=None, params=None):
    """
    Async version of get_db_info.
    Return Database info. Use 'params' for providing arguments.
    For example to include tables in the result, use: params={'include':'tables'}
    """
    if params:
        assert type(params) == dict

    if not db_id:
        if not db_name:
            raise ValueError('Either the name or id of the DB needs to be provided.')
        db_id = await self.get_item_id('database', db_name)

    return await self.get(f"/api/database/{db_id}", params=params)


async def get_table_metadata(self, table_name=None, table_id=None, db_name=None, db_id=None, params=None):
    """Async version of get_table_metadata"""
    if params:
        assert type(params) == dict

    if not table_id:
        if not table_name:
            raise ValueError('Either the name or id of the table needs to be provided.')
        table_id = await self.get_item_id('table', table_name, db_name=db_name, db_id=db_id)

    return await self.get(f"/api/table/{table_id}/query_metadata", params=params)


async def get_columns_name_id(self, table_name=None, db_name=None, table_id=None, db_id=None, verbose=False, column_id_name=False):
    """
    Async version of get_columns_name_id.
    Return a dictionary with col_name key and col_id value, for the given table_id/table_name in the given db_id/db_name.
    If column_id_name is True, return a dictionary with col_id key and col_name value.
    """
    if not await self.friendly_names_is_disabled():
        raise ValueError('Please disable "Friendly Table and Field Names" from Admin Panel > Settings > General, and try again.')

    if not table_name:
        if not table_id:
            raise ValueError('Either the name or id of the table must be provided.')
        table_name = await self.get_item_name(item_type='table', item_id=table_id)

    # Get db_id
    if not db_id:
        if db_name:
            db_id = await self.get_item_id('database', db_name)
        else:
            if not table_id:
                table_id = await self.get_item_id('table', table_name)
            db_id = await self.get_db_id_from_table_id(table_id)

    # Get column names and IDs
    fields = await self.get(f"/api/database/{db_id}/fields")
    if column_id_name:
        return {i['id']: i['name'] for i in fields if i['table_name'] == table_name}
    else:
        return {i['name']: i['id'] for i in fields if i['table_name'] == table_name}


async def friendly_names_is_disabled(self):
    """
    Async version of friendly_names_is_disabled.
    The endpoint /api/database/:db-id/fields which is used in the function get_columns_name_id relies on the display name of fields.
    If "Friendly Table and Field Names" (in Admin Panel > Settings > General) is not disabled, it changes the display name of fields.
    So it is important to make sure this setting is disabled, before running the get_columns_name_id function.
    """
    # checking whether friendly_name is disabled required admin access.
    # So to let non-admin users also use this package we skip this step for them.
    # There is warning in the __init__ method for these users.
    if not self.is_admin:
        return True

    settings = await self.get('/api/setting')
    friendly_name_setting = [i['value'] for i in settings if i['key'] == 'humanization-strategy'][0]
    return friendly_name_setting == 'none'  # 'none' means disabled


@staticmethod
def verbose_print(verbose, msg):
    """Same as the synchronous version - no need for async here"""
    if verbose:
        print(msg)
