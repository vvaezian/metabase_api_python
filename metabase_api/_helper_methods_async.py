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
