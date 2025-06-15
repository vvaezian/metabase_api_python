
async def create_card(self, card_name=None, collection_name=None, collection_id=None, 
                db_name=None, db_id=None, table_name=None, table_id=None, 
                column_order='db_table_order', custom_json=None, verbose=False, return_card=False):
    """
    Async version of create_card.
    Create a card using the given arguments utilizing the endpoint 'POST /api/card/'. 
    If collection is not given, the root collection is used.
    """
    if custom_json:
        assert type(custom_json) == dict
        # Check whether the provided json has the required info or not
        complete_json = True
        for item in ['name', 'dataset_query', 'display']:
            if item not in custom_json:
                complete_json = False
                self.verbose_print(verbose, 'The provided json is detected as partial.')
                break

        # Fix for the issue #10
        if custom_json.get('description') == '': 
            custom_json['description'] = None

        # Set the collection
        if collection_id:
            custom_json['collection_id'] = collection_id
        elif collection_name:
            collection_id = await self.get_item_id('collection', collection_name)
            custom_json['collection_id'] = collection_id

        if complete_json:
            # Add visualization_settings if it is not present in the custom_json
            if 'visualization_settings' not in custom_json:
                custom_json['visualization_settings'] = {}
            # Add the card name if it is provided
            if card_name is not None:
                custom_json['name'] = card_name
            if collection_id:
                custom_json['collection_id'] = collection_id
            elif collection_name:
                collection_id = await self.get_item_id('collection', collection_name)
                custom_json['collection_id'] = collection_id
            if not custom_json.get('collection_id'):
                self.verbose_print(verbose, 'No collection name or id is provided. Will create the card at the root ...')

            # Create the card using only the provided custom_json 
            res = await self.post("/api/card/", json=custom_json)
            if res and not res.get('error'):
                self.verbose_print(verbose, 'The card was created successfully.')
                return res if return_card else None
            else:
                print('Card Creation Failed.\n', res)
                return res

    # Making sure we have the required data
    if not card_name and (not custom_json or not custom_json.get('name')):
        raise ValueError("A name must be provided for the card (either as card_name argument or as part of the custom_json ('name' key)).")
    if not table_id:
        if not table_name:
            raise ValueError('Either the name or id of the table must be provided.')
        table_id = await self.get_item_id('table', table_name, db_id=db_id, db_name=db_name)
    if not table_name:
        table_name = await self.get_item_name(item_type='table', item_id=table_id)
    if not db_id:
        db_id = await self.get_db_id_from_table_id(table_id)

    # Get collection_id if it is not given
    if not collection_id:
        if not collection_name:
            self.verbose_print(verbose, 'No collection name or id is provided. Will create the card at the root ...')
        else:
            collection_id = await self.get_item_id('collection', collection_name)

    if type(column_order) == list:
        column_name_id_dict = await self.get_columns_name_id(
            db_id=db_id, 
            table_id=table_id, 
            table_name=table_name, 
            verbose=verbose
        )
        try:
            column_id_list = [column_name_id_dict[i] for i in column_order]
        except ValueError as e:
            print(f'The column name {e} is not in the table {table_name}. \nThe card creation failed!')
            return False

        column_id_list_str = [['field-id', i] for i in column_id_list]

    elif column_order == 'db_table_order':  # default
        # Find the actual order of columns in the table as they appear in the database
        # Create a temporary card for retrieving column ordering
        json_str = f"""{{
            'dataset_query': {{ 
                'database': {db_id},
                'native': {{'query': 'SELECT * from "{table_name}";' }},
                'type': 'native' 
            }},
            'display': 'table',
            'name': '{card_name}',
            'visualization_settings': {{}} 
        }}"""

        json_dict = eval(json_str.replace("'", '"'))
        res = await self.post("/api/card/", json=json_dict)
        if not res:
            print('Card Creation Failed!')
            return res
            
        ordered_columns = [i['name'] for i in res['result_metadata']]  # retrieving the column ordering

        # Delete the temporary card
        card_id = res['id']
        await self.delete(f"/api/card/{card_id}")

        column_name_id_dict = await self.get_columns_name_id(
            db_id=db_id, 
            table_id=table_id, 
            table_name=table_name, 
            verbose=verbose
        )
        column_id_list = [column_name_id_dict[i] for i in ordered_columns]
        column_id_list_str = [['field-id', i] for i in column_id_list]

    elif column_order == 'alphabetical':
        column_id_list_str = None

    else:
        raise ValueError("Wrong value for 'column_order'. \
                          Accepted values: 'alphabetical', 'db_table_order' or a list of column names.")

    # default json
    json_str = f"""{{
        'dataset_query': {{
            'database': {db_id},
            'query': {{
                'fields': {column_id_list_str},
                'source-table': {table_id}
            }},
            'type': 'query'
        }},
        'display': 'table',
        'name': '{card_name}',
        'collection_id': {collection_id if collection_id else 'null'},
        'visualization_settings': {{}}
    }}"""

    json_dict = eval(json_str.replace("'", '"'))

    # Add/Rewrite data to the default json from custom_json
    if custom_json:
        for key, value in custom_json.items():
            if key in ['name', 'dataset_query', 'display']:
                self.verbose_print(verbose, f"Ignored '{key}' key in the provided custom_json.")
                continue
            json_dict[key] = value

    res = await self.post("/api/card/", json=json_dict)

    # Get collection_name to be used in the final message
    if not collection_name:
        if not collection_id:
            collection_name = 'root'
        else:
            collection_name = await self.get_item_name(item_type='collection', item_id=collection_id)

    if res and not res.get('error'):
        self.verbose_print(verbose, f"The card '{card_name}' was created successfully in the collection '{collection_name}'.")
        if return_card: 
            return res
    else:
        print('Card Creation Failed.\n', res)
        return res


async def create_collection(self, collection_name, parent_collection_id=None, parent_collection_name=None, return_results=False):
    """
    Async version of create_collection.
    Create an empty collection, in the given location, utilizing the endpoint 'POST /api/collection/'. 
    """
    # Making sure we have the data we need
    if not parent_collection_id:
        if not parent_collection_name:
            print('Either the name of id of the parent collection must be provided.')
        if parent_collection_name == 'Root':
            parent_collection_id = None
        else:
            parent_collection_id = await self.get_item_id('collection', parent_collection_name)

    res = await self.post('/api/collection', json={'name': collection_name, 'parent_id': parent_collection_id, 'color': '#509EE3'})
    if return_results:
        return res


async def create_segment(self, segment_name, column_name, column_values, segment_description='', 
                    db_name=None, db_id=None, table_name=None, table_id=None, return_segment=False):
    """
    Async version of create_segment.
    Create a segment using the given arguments utilizing the endpoint 'POST /api/segment/'.
    """
    # Making sure we have the data needed
    if not table_name and not table_id:
        raise ValueError('Either the name or id of the table must be provided.')
    if not table_id:
        table_id = await self.get_item_id('table', table_name, db_id=db_id, db_name=db_name)
    if not table_name:
        table_name = await self.get_item_name(item_type='table', item_id=table_id)
    db_id = await self.get_db_id_from_table_id(table_id)

    colmuns_name_id_mapping = await self.get_columns_name_id(table_name=table_name, db_id=db_id)
    column_id = colmuns_name_id_mapping[column_name]

    # Create a segment blueprint
    segment_blueprint = {
        'name': segment_name,
        'description': segment_description,
        'table_id': table_id,
        'definition': {'source-table': table_id, 'filter': ['=', ['field-id', column_id]]}
    }

    # Add filtering values
    segment_blueprint['definition']['filter'].extend(column_values)

    # Create the segment
    res = await self.post('/api/segment/', json=segment_blueprint)
    if return_segment:
        return res
