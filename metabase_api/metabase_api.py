import requests
import getpass

class Metabase_API():
  
  def __init__(self, domain, email, password=None):
    
    self.domain = domain
    self.email = email
    self.password = getpass.getpass(prompt='Please enter your password: ') if password is None else password
    self.session_id = None
    self.header = None
    self.authenticate()
  
  
  def authenticate(self):
    """Get a Session ID"""
    conn_header = {'username':self.email,
                   'password':self.password}

    res = requests.post(self.domain + '/api/session', json = conn_header)
    if not res.ok:
      raise Exception(res)
    
    self.session_id = res.json()['id']
    self.header = {'X-Metabase-Session':self.session_id}
  
  
  def validate_session(self):
    """Get a new session ID if the previous one has expired"""
    res = requests.get(self.domain + '/api/user/current', headers = self.header)
    
    if res.ok:  # 200
      return True
    elif res.unauthorized:  # 401
      return self.authenticate()
    else:
      raise Exception(res)
  
  
  ##### REST Methods #####
  def get(self, endpoint, **kwargs):
    self.validate_session()
    res = requests.get(self.domain + endpoint, headers=self.header, **kwargs)
    return res.json() if res.ok else False
  
  
  def post(self, endpoint, **kwargs):
    self.validate_session()
    res = requests.post(self.domain + endpoint, headers=self.header, **kwargs)
    return res.json() if res.ok else False
  
  
  def put(self, endpoint, **kwargs):
    """Used for updating objects (cards, dashboards, ...)"""
    self.validate_session()
    res = requests.put(self.domain + endpoint, headers=self.header, **kwargs)
    return res.status_code
  
  
  def delete(self, endpoint, **kwargs):
    self.validate_session()
    res = requests.delete(self.domain + endpoint, headers=self.header, **kwargs)
    return res.status_code
  
  
  
  ##### Custom Functions #####
  def move_to_archive(self, card_name=None, collection_name=None, card_id=None, verbose=False):
    if not card_id:
      if not card_name:
        raise ValueError('Either the name or id of the card must be provided.')
      card_id = self.get_card_id(card_name, collection_name)
    
    res = self.put('/api/card/{}'.format(card_id), json={'archived':True})
    self.verbose_print(verbose, 'Successfully Archived.') if res == 200 else print('Archiving Failed.')
    
    return res
  
  
  def get_collection_id(self, collection_name):
    collection_IDs = [ i['id'] for i in self.get("/api/collection/") if i['name'] == collection_name ]
    
    if len(collection_IDs) > 1:
      raise KeyError('There is more than one collection with the name {}'.format(collection_name))
    if len(collection_IDs) == 0:
      raise ValueError('There is no collection with the name {}'.format(collection_name))
    
    return collection_IDs[0] 

  
  def get_db_id(self, db_name):
    db_IDs = [ i['id'] for i in self.get("/api/database/") if i['name'] == db_name ]
    
    if len(db_IDs) > 1:
      raise KeyError('There is more than one DB with the name {}'.format(db_name))
    if len(db_IDs) == 0:
      raise ValueError('There is no DB with the name {}'.format(db_name))
    
    return db_IDs[0]
  
  
  def get_db_id_from_table_name(self, table_name):
    tables = [(i['name'], i['db']['id']) for i in self.get("/api/table/") if i['name'] == table_name]
    
    if len(tables) > 1:
      raise KeyError('There is more than one DB containing the table name {}. Please provide the DB name or id as well.'.format(table_name))
    if len(tables) == 0:
      raise ValueError('There is no DB containing the table {}'.format(table_name))
    
    return tables[0][1]
  
  
  
  def get_table_id(self, table_name, db_name=None, db_id=None):
    tables = self.get("/api/table/")
    
    if db_id:
      table_IDs = [ i['id'] for i in tables if i['name'] == table_name and i['db']['id'] == db_id ]
    elif db_name:
      table_IDs = [ i['id'] for i in tables if i['name'] == table_name and i['db']['name'] == db_name ]
    else:
      table_IDs = [ i['id'] for i in tables if i['name'] == table_name ]
      
    if len(table_IDs) > 1:
      raise KeyError('There is more than one table with the name {} (in the provided db, if any)'.format(table_name))
    if len(table_IDs) == 0:
      raise ValueError('There is no table with the name {} (in the provided db, if any)'.format(table_name))
    
    return table_IDs[0]
  
  
  def get_card_id(self, card_name, collection_name=None, collection_id=None):
    if not collection_id:
      if not collection_name:
        print('Collection is not given, searching in all collections ... (to search only in the root, \
               provide the name "root" for collection_name)')
        card_IDs = [ i['id'] for i in self.get("/api/card/") if i['name'] == card_name 
                                                            and i['archived'] == False ]
      else:
        collection_id = self.get_collection_id(collection_name) if collection_name != 'root' else None
        card_IDs = [ i['id'] for i in self.get("/api/card/") if i['name'] == card_name 
                                                            and i['collection_id'] == collection_id 
                                                            and i['archived'] == False ]
    else:
      card_IDs = [ i['id'] for i in self.get("/api/card/") if i['name'] == card_name 
                                                          and i['collection_id'] == collection_id 
                                                          and i['archived'] == False ]
    
    if len(card_IDs) > 1:
      raise KeyError('There is more than one card with the name "{}" in the collection "{}"'.format(card_name, collection_name))
    if len(card_IDs) == 0:
      if not collection_name:
          raise ValueError('There is no card with the name "{}"'.format(card_name, collection_name))
      raise ValueError('There is no card with the name "{}" in the collection "{}"'.format(card_name, collection_name))
    
    return card_IDs[0]
  
  
  def get_collection_name(self, collection_id):
    collections = self.get("/api/collection/")
    collection_name = [ i.get('slug', 'root') for i in collections if i['id'] == collection_id ]
    if len(collection_name) == 0:
      raise ValueError('There is no collection with the id {}'.format(collection_id))

    return collection_name[0]

  
  def get_table_name(self, table_id):
    tables = self.get("/api/table/")
    table_name = [i['name'] for i in tables if i['id'] == table_id]
    if len(table_name) == 0:
      raise ValueError('There is no table with the id {}'.format(table_id))
    
    return table_name[0]
  
  
  @staticmethod
  def verbose_print(verbose, msg):
    if verbose:
      print(msg)
  
  
  def get_columns_name_id(self, table_name=None, db_name=None, table_id=None, db_id=None, verbose=False):
    '''Return a dictionary with col_id key and col_name value, for the given table_id/table_name in the given db_id/db_name'''
    if not db_id:
      if not db_name:
        raise ValueError('Either the name or id of the db must be provided.')
      self.verbose_print(verbose, 'Getting db_id ...')
      db_id = self.get_db_id(db_name)
      
    if not table_name:
      if not table_id:
        raise ValueError('Either the name or id of the table must be provided.')
      self.verbose_print(verbose, 'Getting table_name ...')
      table_name = self.get_table_name(table_id)
    
    self.verbose_print(verbose, "Getting column names and id's ...")
    return {i['name']: i['id'] for i in self.get("/api/database/{}/fields".format(db_id)) if i['table_name'] == table_name}

  
  def create_card(self, card_name=None, collection_name=None, collection_id=None, 
                  db_name=None, db_id=None, table_name=None,  table_id=None, 
                  column_order='db_table_order', custom_json=None, verbose=False):
    """Create a card using the given arguments utilizing the endpoint 'POST /api/card/'.
    
    Keyword arguments:
    card_name -- the name used to create the card (default None) 
    collection_name -- name of the collection to place the card (default None).
    collection_id -- id of the collection to place the card (default None) 
    db_name -- name of the db that is used as the source of data (default None) 
    table_name -- name of the table used as the source of data (default None) 
    db_id -- id of the db used as the source of data (default None) 
    table_id -- id of the table used as the source of data (default None) 
    column_order -- order for showing columns. Accepted values are 'alphabetical', 'db_table_order' (default) 
                    or a list of column names
    custom_json -- key-value pairs that can provide some or all the data needed for creating the card (default None).
                   If you are providing only this argument, the keys 'name', 'dataset_query' and 'display' are required
                   (https://github.com/metabase/metabase/blob/master/docs/api-documentation.md#post-apicard).
                   Although the key 'visualization_settings' is also required for the endpoint, since it can be an 
                   empty dict ({}), if it is absent in the provided json, the function adds it automatically. 
    verbose -- print extra information (default False) 
    """
    if custom_json:
      complete_json = True
      for item in ['name', 'dataset_query', 'display']:
        if item not in custom_json:
          complete_json = False
          self.verbose_print(verbose, 'The provided json is detected as partial.')
          break
      
      if complete_json:
        # Adding visualization_settings if it is not present in the custom_json
        if 'visualization_settings' not in custom_json:
          custom_json['visualization_settings'] = {}
          
        self.verbose_print(verbose, "Creating the card using only the provided custom_json ...") 
        res = self.post("/api/card/", json=custom_json)
        self.verbose_print(verbose, 'Card Created Successfully.') if res else print('Card Creation Failed.')
        
        return res
    
    # getting table_id
    if not table_id:
      if not table_name:
        raise ValueError('Either the name or id of the table must be provided.')
      if not db_id:
        if not db_name:
          self.verbose_print(verbose, "Getting table_id ...")
          table_id = self.get_table_id(table_name)
          db_id = self.get_db_id_from_table_name(table_name)
        else:
          self.verbose_print(verbose, "Getting db_id ...")
          db_id = self.get_db_id(db_name)
          self.verbose_print(verbose, "Getting table_id ...")
          table_id = self.get_table_id(table_name=table_name, db_id=db_id)
      else:
        self.verbose_print(verbose, "Getting table_id ...")
        table_id = self.get_table_id(table_name, db_id=db_id)
    else:
      if not table_name:
        table_name = self.get_table_name(table_id)
    
    # getting collection_id if a collection is specified
    if not collection_id:
      if not collection_name:
        self.verbose_print(verbose, 'No collection name or id is provided. Will create the card in the root ...')
      else:
        self.verbose_print(verbose, "Getting collection_id ...")
        collection_id = self.get_collection_id(collection_name)
    
    if type(column_order) == list:
      column_name_id_dict = self.get_columns_name_id(db_id=db_id, table_id=table_id, table_name=table_name, verbose=verbose)
      try:
        column_id_list = [column_name_id_dict[i] for i in column_order]
      except KeyError as e:
        print('The column name {} is not in the table {}. \nThe card creation failed!'.format(e, table_name))
        return

      column_id_list_str = [['field-id', i] for i in column_id_list]

    elif column_order == 'db_table_order':  # default
      self.verbose_print(verbose, "Finding the actual order of columns in the table as they appear in the database ...")
      # creating a temporary card for retrieving column ordering
      json_str = """{{'dataset_query': {{'database': {1},
                                    'native': {{'query': 'SELECT * from "{2}";' }},
                                    'type': 'native' }},
              'display': 'table',
              'name': '{0}',
              'visualization_settings': {{}} }}""".format(card_name, db_id, table_name)
      
      res = self.post("/api/card/", json=eval(json_str))  
      if not res:
        print('Card Creation Failed!')
        return
      ordered_columns = [ i['name'] for i in res['result_metadata'] ]  # retrieving the column ordering
    
      # deleting the temporary card
      card_id = res['id']
      self.delete("/api/card/{}".format(card_id))  
      
      column_name_id_dict = self.get_columns_name_id(db_id=db_id, table_id=table_id, table_name=table_name, verbose=verbose)
      column_id_list = [column_name_id_dict[i] for i in ordered_columns]
      column_id_list_str = [['field-id', i] for i in column_id_list]
    
    elif column_order == 'alphabetical':
      column_id_list_str = None
    
    else:
      raise ValueError("Wrong value for 'column_order'. Accepted values: 'alphabetical', 'db_table_order' or a list of column names.")
    
    # default json
    json_str = """{{'dataset_query': {{'database': {1},
                                      'query': {{'fields': {4},
                                                 'source-table': {2}}},
                                      'type': 'query'}},
                   'display': 'table',
                   'name': '{0}',
                   'collection_id': {3},
                   'visualization_settings': {{}}
                   }}""".format(card_name, db_id, table_id, collection_id, column_id_list_str)
    json = eval(json_str)
    
    # adding/rewriting data to the default json from custom_json
    if custom_json:
      self.verbose_print(verbose, 'Reading and applying the provided custom_json ...')
      for key, value in custom_json.items():
        if key in ['name', 'dataset_query', 'display']:
          self.verbose_print(verbose, "Ignored '{}' key in the provided custom_json.".format(key))
          continue
        json[key] = value
    
    self.verbose_print(verbose, "Creating the card ...") 
    res = self.post("/api/card/", json=json)
    
    # getting collection_name to be used in the final message
    if not collection_name:
      if not collection_id:
        collection_name = 'root'
      else:
        collection_name = self.get_collection_name(collection_id)
    
    if res and not res.get('error'):
      self.verbose_print(verbose, "The card '{}' was created successfully in the collection '{}'.".format(card_name, collection_name))
      #return res
    else:
      print('Card Creation Failed.\n', res)
      return res
  
  
  @staticmethod
  def make_json(raw_json, prettyprint=False):
    """Turn the string copied from the Inspect->Network window into a Dict."""
    json = eval(raw_json.replace('null', 'None') \
                        .replace('false', 'False')
               )
    if prettyprint:
      import pprint
      pprint.pprint(json)
    return json
