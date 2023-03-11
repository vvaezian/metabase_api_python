
def get_item_info(self, item_type
                , item_id=None, item_name=None
                , collection_id=None, collection_name=None
                , params=None):
    '''
    Return the info for the given item.
    Use 'params' for providing arguments. E.g. to include tables in the result for databases, use: params={'include':'tables'}
    '''    

    assert item_type in ['database', 'table', 'card', 'collection', 'dashboard', 'pulse', 'segment']

    if params:
        assert type(params) == dict

    if not item_id:
        if not item_name:
            raise ValueError('Either the name or id of the {} must be provided.'.format(item_type))
        item_id = self.get_item_id(item_type, item_name, collection_id=collection_id, collection_name=collection_name)

    res = self.get("/api/{}/{}".format(item_type, item_id), params=params)
    if res:
        return res
    else:
        raise ValueError('There is no {} with the id "{}"'.format(item_type, item_id))



def get_item_name(self, item_type, item_id):

    assert item_type in ['database', 'table', 'card', 'collection', 'dashboard', 'pulse', 'segment']

    res = self.get("/api/{}/{}".format(item_type, item_id))
    if res:
        return res['name']
    else:
        raise ValueError('There is no {} with the id "{}"'.format(item_type, item_id))



def get_item_id(self, item_type, item_name, collection_id=None, collection_name=None, db_id=None, db_name=None, table_id=None):

    assert item_type in ['database', 'table', 'card', 'collection', 'dashboard', 'pulse', 'segment']

    if item_type in ['card', 'dashboard', 'pulse']:
        if not collection_id:
            if not collection_name:
                # Collection name/id is not provided. Searching in all collections 
                item_IDs = [ i['id'] for i in self.get("/api/{}/".format(item_type)) if i['name'] == item_name 
                                                                                    and i['archived'] == False ]
            else:
                collection_id = self.get_item_id('collection', collection_name) if collection_name != 'root' else None
                item_IDs = [ i['id'] for i in self.get("/api/{}/".format(item_type)) if i['name'] == item_name 
                                                                                    and i['collection_id'] == collection_id 
                                                                                    and i['archived'] == False ]
        else:
            collection_name = self.get_item_name('collection', collection_id)
            item_IDs = [ i['id'] for i in self.get("/api/{}/".format(item_type)) if i['name'] == item_name 
                                                                                and i['collection_id'] == collection_id 
                                                                                and i['archived'] == False ]

        if len(item_IDs) > 1:
            if not collection_name:
                raise ValueError('There is more than one {} with the name "{}".\n\
                        Provide collection id/name to limit the search space'.format(item_type, item_name))
            raise ValueError('There is more than one {} with the name "{}" in the collection "{}"'
                            .format(item_type, item_name, collection_name))
        if len(item_IDs) == 0:
            if not collection_name:
                    raise ValueError('There is no {} with the name "{}"'.format(item_type, item_name))
            raise ValueError('There is no item with the name "{}" in the collection "{}"'
                            .format(item_name, collection_name))

        return item_IDs[0] 


    if item_type == 'collection':
        collection_IDs = [ i['id'] for i in self.get("/api/collection/") if i['name'] == item_name ]

        if len(collection_IDs) > 1:
            raise ValueError('There is more than one collection with the name "{}"'.format(item_name))
        if len(collection_IDs) == 0:
            raise ValueError('There is no collection with the name "{}"'.format(item_name))

        return collection_IDs[0] 


    if item_type == 'database':
        res = self.get("/api/database/")
        if type(res) == dict:  # in Metabase version *.40.0 the format of the returned result for this endpoint changed
            res = res['data']
        db_IDs = [ i['id'] for i in res if i['name'] == item_name ]

        if len(db_IDs) > 1:
            raise ValueError('There is more than one DB with the name "{}"'.format(item_name))
        if len(db_IDs) == 0:
            raise ValueError('There is no DB with the name "{}"'.format(item_name))

        return db_IDs[0]


    if item_type == 'table':
        tables = self.get("/api/table/")

        if db_id:
            table_IDs = [ i['id'] for i in tables if i['name'] == item_name and i['db']['id'] == db_id ]
        elif db_name:
            table_IDs = [ i['id'] for i in tables if i['name'] == item_name and i['db']['name'] == db_name ]
        else:
            table_IDs = [ i['id'] for i in tables if i['name'] == item_name ]

        if len(table_IDs) > 1:
            raise ValueError('There is more than one table with the name {}. Provide db id/name.'.format(item_name))
        if len(table_IDs) == 0:
            raise ValueError('There is no table with the name "{}" (in the provided db, if any)'.format(item_name))

        return table_IDs[0]


    if item_type == 'segment':
        segment_IDs = [ i['id'] for i in self.get("/api/segment/") if i['name'] == item_name 
                                                                    and (not table_id or i['table_id'] == table_id) ]
        if len(segment_IDs) > 1:
            raise ValueError('There is more than one segment with the name "{}"'.format(item_name))
        if len(segment_IDs) == 0:
            raise ValueError('There is no segment with the name "{}"'.format(item_name))

        return segment_IDs[0]



def get_collection_id(self, collection_name):
    import warnings
    warnings.warn("The function get_collection_id will be removed in the next version. Use get_item_id function instead.", DeprecationWarning)

    collection_IDs = [ i['id'] for i in self.get("/api/collection/") if i['name'] == collection_name ]

    if len(collection_IDs) > 1:
        raise ValueError('There is more than one collection with the name "{}"'.format(collection_name))
    if len(collection_IDs) == 0:
        raise ValueError('There is no collection with the name "{}"'.format(collection_name))

    return collection_IDs[0] 



def get_db_id(self, db_name):
    import warnings
    warnings.warn("The function get_db_id will be removed in the next version. Use get_item_id function instead.", DeprecationWarning)

    res = self.get("/api/database/")
    if type(res) == dict:  # in Metabase version *.40.0 the format of the returned result for this endpoint changed
        res = res['data']
    db_IDs = [ i['id'] for i in res if i['name'] == db_name ]

    if len(db_IDs) > 1:
        raise ValueError('There is more than one DB with the name "{}"'.format(db_name))
    if len(db_IDs) == 0:
        raise ValueError('There is no DB with the name "{}"'.format(db_name))

    return db_IDs[0]



def get_table_id(self, table_name, db_name=None, db_id=None):
    import warnings
    warnings.warn("The function get_table_id will be removed in the next version. Use get_item_id function instead.", DeprecationWarning)

    tables = self.get("/api/table/")

    if db_id:
        table_IDs = [ i['id'] for i in tables if i['name'] == table_name and i['db']['id'] == db_id ]
    elif db_name:
        table_IDs = [ i['id'] for i in tables if i['name'] == table_name and i['db']['name'] == db_name ]
    else:
        table_IDs = [ i['id'] for i in tables if i['name'] == table_name ]

    if len(table_IDs) > 1:
        raise ValueError('There is more than one table with the name {}. Provide db id/name.'.format(table_name))
    if len(table_IDs) == 0:
        raise ValueError('There is no table with the name "{}" (in the provided db, if any)'.format(table_name))

    return table_IDs[0]



def get_segment_id(self, segment_name, table_id=None):
    import warnings
    warnings.warn("The function get_segment_id will be removed in the next version. Use get_item_id function instead.", DeprecationWarning)

    segment_IDs = [ i['id'] for i in self.get("/api/segment/") if i['name'] == segment_name 
                                                                and (not table_id or i['table_id'] == table_id) ]
    if len(segment_IDs) > 1:
        raise ValueError('There is more than one segment with the name "{}"'.format(segment_name))
    if len(segment_IDs) == 0:
        raise ValueError('There is no segment with the name "{}"'.format(segment_name))

    return segment_IDs[0]



def get_db_id_from_table_id(self, table_id):
    tables = [ i['db_id'] for i in self.get("/api/table/") if i['id'] == table_id ]

    if len(tables) == 0:
        raise ValueError('There is no DB containing the table with the ID "{}"'.format(table_id))

    return tables[0]



def get_db_info(self, db_name=None, db_id=None, params=None):
    '''
    Return Database info. Use 'params' for providing arguments.
    For example to include tables in the result, use: params={'include':'tables'}
    '''
    import warnings
    warnings.warn("The function get_db_info will be removed in the next version. Use get_item_info function instead.", DeprecationWarning)

    if params:
        assert type(params) == dict

    if not db_id:
        if not db_name:
            raise ValueError('Either the name or id of the DB needs to be provided.')
        db_id = self.get_item_id('database', db_name)

    return self.get("/api/database/{}".format(db_id), params=params)



def get_table_metadata(self, table_name=None, table_id=None, db_name=None, db_id=None, params=None):

    if params:
        assert type(params) == dict

    if not table_id:
        if not table_name:
            raise ValueError('Either the name or id of the table needs to be provided.')
        table_id = self.get_item_id('table', table_name, db_name=db_name, db_id=db_id)

    return self.get("/api/table/{}/query_metadata".format(table_id), params=params)



def get_columns_name_id(self, table_name=None, db_name=None, table_id=None, db_id=None, verbose=False, column_id_name=False):
    '''
    Return a dictionary with col_name key and col_id value, for the given table_id/table_name in the given db_id/db_name.
    If column_id_name is True, return a dictionary with col_id key and col_name value.
    '''
    if not self.friendly_names_is_disabled():
        raise ValueError('Please disable "Friendly Table and Field Names" from Admin Panel > Settings > General, and try again.')

    if not table_name:
        if not table_id:
            raise ValueError('Either the name or id of the table must be provided.')
        table_name = self.get_item_name(item_type='table', item_id=table_id)

    # Get db_id
    if not db_id:
        if db_name:
            db_id = self.get_item_id('database', db_name)
        else:
            if not table_id:
                table_id = self.get_item_id('table', table_name)
            db_id = self.get_db_id_from_table_id(table_id)

    # Get column names and IDs 
    if column_id_name:
        return {i['id']: i['name'] for i in self.get("/api/database/{}/fields".format(db_id)) 
                                                                if i['table_name'] == table_name}
    else:
        return {i['name']: i['id'] for i in self.get("/api/database/{}/fields".format(db_id)) 
                                                                if i['table_name'] == table_name}



def friendly_names_is_disabled(self):
    '''
    The endpoint /api/database/:db-id/fields which is used in the function get_columns_name_id relies on the display name of fields. 
    If "Friendly Table and Field Names" (in Admin Panel > Settings > General) is not disabled, it changes the display name of fields.
    So it is important to make sure this setting is disabled, before running the get_columns_name_id function.
    '''
    # checking whether friendly_name is disabled required admin access. 
    # So to let non-admin users also use this package we skip this step for them.
    # There is warning in the __init__ method for these users.
    if not self.is_admin:  
        return True

    friendly_name_setting = [ i['value'] for i in self.get('/api/setting') if i['key'] == 'humanization-strategy' ][0]
    return friendly_name_setting == 'none'  # 'none' means disabled



def get_field_ref_id(field):
    """
    :return:
    """
    field_ref = field['field_ref']
    if isinstance(field_ref, list) and (len(field_ref) >= 2):
        field_type = field_ref[0]
        if field_type == 'field':
            field_name = field_ref[1]
            return f'["ref",["field",{field_name},null]]'
        elif field_type == 'aggregation':
            # It seems that Metabase server could guarantee unique name when using aggregation.
            # Experiment shows that when 2 aggregation calc is same type e.g. sum,
            # the 1st is 'sum', the 2nd is 'sum_2'
            field_name = field['name']
            return f'["name","{field_name}"]'
    else:
        raise Exception('Get field ref id failed, check data structure please.')


def get_visual_title(field, column_settings, is_weak=False):
    """
    :param field: dict, key named 'field_ref' is requisite for all conditions, key named 'name' is requisite when aggregation
    :param column_settings:
    :param is_weak: when visual setting not found: return None if is_weak, else raise exception
    :return:
    """
    column_key = get_field_ref_id(field)
    column_visual_setting = column_settings.get(column_key)
    if not column_visual_setting:
        if is_weak:
            return None
        else:
            raise ValueError(f'request weak mode in column_settings, while got None for field: {field}')
    return column_visual_setting['column_title']


def get_visual_table(raw_table, column_settings):
    """
    Rename columns and adjust value positions according to column_settings in visualization_settings of query_metadata
    Currently, possible adjustments include:
    - remapping: each 1 mapping results in 2 fields in raw_table['rows'], in which one is original,
      the other is target value. The former will be dropped and the latter will be picked.

    :param raw_table: dict, with keys: 'rows', 'cols '
    :param column_settings: list of dict, query_metadata['visualization_settings']['column_settings']
    :return: visual_table, dict, with keys: 'rows', 'cols'
    """
    visual_columns = []  # collect visual column names returned, e.g. ['col1_vis', 'col2_vis']
    valid_indexes = []  # collect actual data positions returned, e.g. [['ab', 1], ['cd', 2]]

    # Possible field_ref:
    #
    #    ['field', 712, {'join-alias': 'some-table-name'}]
    #    ['aggregation', 'sum']
    #    ['aggregation', 'sum_2']
    #
    # Not every column dict has key 'field_ref'.
    # Those who has do NOT necessarily has corresponding value in column_settings.
    # column_settings is a dict, mapping from :field_ref string, to a setting dict.
    #
    # If :field_ref string ...
    # DO found in column_settings => 'column_title' in dict is what we want
    # NOT found in column_settings => remapping may exist => use 'display_name' instead
    #
    # To check remapping info, use data -> cols info in response from /api/card/:card_id/query
    # If 'remapped_from' or 'remapped_to' in the field, then that must be a field with remapping info

    ### visual_columns ### # noqa
    # remapping: str -> dict
    # [key] index of remapped_from
    # [value] {'from_name', 'from_raw', 'to_index', 'to_name', 'to_raw'}
    remapping = dict()
    raw_cols = raw_table['cols']
    for col_index, r_col in enumerate(raw_cols):
        field_ref = r_col.get('field_ref')
        col_name = r_col['name']
        if field_ref is None:
            may_from_name = r_col.get('remapped_from')
            if (may_from_name in remapping) and (col_name == remapping[may_from_name]['to_name']):
                remapping[may_from_name].update({
                    'to_index': col_index,
                    'to_raw': dict(r_col),
                })
            else:
                from warnings import warn
                warn('Visualization enabled in Metabase card query,'
                     'while field with name [{}] does NOT have field_ref, which may cause problems.'.format(col_name),
                     Warning)
        else:
            may_to_name = r_col.get('remapped_to')
            if may_to_name:
                remapping[col_name] = {
                    'from_index': col_index,
                    'to_name': may_to_name,
                    'from_raw': dict(r_col),
                }
                visual_columns.append(None)
                valid_indexes.append(None)
            else:
                visual = get_visual_title(r_col, column_settings, is_weak=True) or r_col['display_name']
                visual_columns.append(visual)
                valid_indexes.append(col_index)

    ### valid_indexs ###  # noqa
    for null_visual_name, info in remapping.items():
        null_visual_index = info['from_index']
        visual_sub = info['to_raw']['display_name']
        visual_columns[null_visual_index] = visual_sub
        valid_indexes[null_visual_index] = info['to_index']

    raw_rows = raw_table['rows']
    valid_rows = [
        [r_row[index] for index in valid_indexes] for r_row in raw_rows
    ]
    visual_table = {'rows': valid_rows, 'cols': visual_columns}
    return visual_table



@staticmethod
def verbose_print(verbose, msg):
    if verbose:
        print(msg)
