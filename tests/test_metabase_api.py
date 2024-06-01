from metabase_api.metabase_api import Metabase_API
import datetime
import unittest


mb = Metabase_API('http://localhost:3000', 'abc.xyz@gmail.com', 'xzy12345')


class Metabase_API_Test(unittest.TestCase):
  
  from collections import defaultdict
  cleanup_objects = defaultdict(list)


  def setUp(self):  # runs before every test
    pass


  def tearDown(self):  # runs after every test
    for item_type, item_id_list in Metabase_API_Test.cleanup_objects.items():
      if item_type in ['card', 'dashboard', 'pulse']:
        for item_id in item_id_list:
          mb.delete_item(item_type=item_type, item_id=item_id)
      if item_type in ['collection', 'segment']:  # these cannot be deleted, so we archive them
        for item_id in item_id_list:
          mb.move_to_archive(item_type=item_type, item_id=item_id)
      



  ### Testing the Helper Functions
  
  def test_get_item_info(self):
    # database
    res = mb.get_item_info('database', 2)
    self.assertEqual(res['name'], 'test_db')
    self.assertEqual(res['id'], 2)

    # table
    res = mb.get_item_info('table', 9)
    self.assertEqual(res['name'], 'test_table2')
    self.assertEqual(res['id'], 9)

    # card
    res = mb.get_item_info('card', 1)
    self.assertEqual(res['name'], 'test_card')
    self.assertEqual(res['id'], 1)

    # collection
    res = mb.get_item_info('collection', 2)
    self.assertEqual(res['name'], 'test_collection')
    self.assertEqual(res['id'], 2)

    # dashboard
    res = mb.get_item_info('dashboard', 1)
    self.assertEqual(res['name'], 'test_dashboard')
    self.assertEqual(res['id'], 1)



  def test_get_item_name(self):
    # database
    db_name = mb.get_item_name('database', 2)
    self.assertEqual(db_name, 'test_db')

    # table
    table_name = mb.get_item_name('table', 9)
    self.assertEqual(table_name, 'test_table2')

    # card
    card_name = mb.get_item_name('card', 1)
    self.assertEqual(card_name, 'test_card')

    # collection
    collection_name = mb.get_item_name('collection', 2)
    self.assertEqual(collection_name, 'test_collection')

    # dashboard
    dashboard_name = mb.get_item_name('dashboard', 1)
    self.assertEqual(dashboard_name, 'test_dashboard')



  def test_get_item_id(self):
    # database
    db_id = mb.get_item_id('database', 'test_db')
    self.assertEqual(db_id, 2)

    # table
    table_id = mb.get_item_id('table', 'test_table')
    self.assertEqual(table_id, 10)

    # card
    card_id = mb.get_item_id('card', 'test_card')
    self.assertEqual(card_id, 1)

    # collection
    collection_id = mb.get_item_id('collection', 'test_collection')
    self.assertEqual(collection_id, 2)

    with self.assertRaises(ValueError) as error:
      mb.get_item_id('collection', 'test_collection_dup')  
    self.assertEqual(str(error.exception), 'There is more than one collection with the name "test_collection_dup"')

    with self.assertRaises(ValueError) as error:
      mb.get_item_id('collection', 'xyz')  
    self.assertEqual(str(error.exception), 'There is no collection with the name "xyz"')

    # dashboard
    dashboard_id = mb.get_item_id('dashboard', 'test_dashboard')
    self.assertEqual(dashboard_id, 1)



  def test_get_db_id_from_table_id(self):
    db_id = mb.get_db_id_from_table_id(9)
    self.assertEqual(db_id, 2)



  def test_get_table_metadata(self):
    table_info = mb.get_table_metadata(table_id=9)
    self.assertEqual(table_info['fields'][0]['name'], 'col1')



  def test_get_columns_name_id(self):
    name_id_mapping = mb.get_columns_name_id(table_id=8)  # table with id 8 is the products table from sample dataset
    self.assertEqual(name_id_mapping['CATEGORY'], 64)

    id_name_mapping = mb.get_columns_name_id(table_id=8, column_id_name=True)
    self.assertEqual(id_name_mapping[64], 'CATEGORY')



  ### Testing the Custom Functions

  def test_create_card(self):
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    res1 = mb.create_card(card_name=f'test_create_card_{t}', table_name='test_table', collection_id=2, return_card=True)

    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    card_info = {
      'name': f'test_create_card_json1_{t}',
      'display': 'table',
      'dataset_query': {
        'database': 2,
        'native': { 'query': 'select * from test_table' },
        'type': 'native' 
      },
      'collection_id':2
    }
    res2 = mb.create_card(custom_json=card_info, return_card=True)
    Metabase_API_Test.cleanup_objects['card'].append(res2['id'])
    
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    card_info = {
      'name': f'test_create_card_json2_{t}',
      'display': 'table',
      'dataset_query': {
        'database': 2,
        'native': { 'query': 'select * from test_table' },
        'type': 'native' 
      }
    }
    res3 = mb.create_card(custom_json=card_info, collection_id=2, return_card=True)
    Metabase_API_Test.cleanup_objects['card'].append(res3['id'])

    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    card_info = {
      'name': f'test_create_card_json3_{t}',
      #'display': 'table',
      'dataset_query': {
        'database': 2,
        'native': { 'query': 'select * from test_table' },
        'type': 'native' 
      }
    }
    with self.assertRaises(ValueError) as error:
      mb.create_card(custom_json=card_info, collection_id=2)
    self.assertEqual(str(error.exception), 'Either the name or id of the table must be provided.')

    # check to make sure the cards were created in the right collection
    collection_IDs_of_created_cards = { i['collection_id'] for i in [res1, res2, res3] }
    self.assertEqual(collection_IDs_of_created_cards, set({2}))

    # add id of the created cards to the cleaup list to be taken care of by the tearDown method
    Metabase_API_Test.cleanup_objects['card'].extend([ res1['id'], res3['id'], res3['id'] ])



  def test_create_collection(self):
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    res = mb.create_collection(f'test_create_collection {t}', parent_collection_id=2, return_results=True)

    # check to make sure the collection was created in the right place
    res2 = mb.get('/api/collection/{}'.format(res['id']))
    self.assertEqual(res2['parent_id'], 2)

    # add to cleanup list
    Metabase_API_Test.cleanup_objects['collection'].append(res['id'])



  def test_copy_card(self):
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    newCard_id = mb.copy_card(source_card_id=1, destination_collection_id=1, destination_card_name='test_copy_card_{}'.format(t))
    
    # make sure the cards were created in the right collection
    res = mb.get('/api/card/{}'.format(newCard_id))
    self.assertEqual(res['collection_id'], 1)
    
    # add to cleanup list
    Metabase_API_Test.cleanup_objects['card'].append(res['id'])



  def test_copy_dashboard(self):
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # shallow copy
    dup_dashboard_id_shallow = mb.copy_dashboard(source_dashboard_id=1, destination_collection_id=1, postfix='_dup_shallow_{}'.format(t))

    # deep copy
    dup_dashboard_id_deep = mb.copy_dashboard(source_dashboard_id=1, destination_collection_id=1, postfix='_dup_deep_{}'.format(t), deepcopy=True)
    new_collection_id = mb.get_item_id('collection', "test_dashboard_dup_deep_{}'s cards".format(t))

    # add to cleanup list
    Metabase_API_Test.cleanup_objects['dashboard'].extend([dup_dashboard_id_shallow, dup_dashboard_id_deep])
    Metabase_API_Test.cleanup_objects['collection'].append(new_collection_id)



  def test_copy_collection(self):
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    mb.copy_collection(source_collection_id=3, destination_parent_collection_id=1, destination_collection_name='test_copy_collection_{}'.format(t))
    new_collection_id = mb.get_item_id('collection', 'test_copy_collection_{}'.format(t))

    # add to cleanup list
    Metabase_API_Test.cleanup_objects['collection'].append(new_collection_id)



  def test_search(self):
    res = mb.search('test_db')
    self.assertEqual(len(res), 1)
    self.assertEqual(res[0]['model'], 'database')



  def test_get_card_data(self):
    # json
    res = mb.get_card_data(card_id=1)
    json_data = [
      {'col1': 'row1 cell1', 'col2': 1},
      {'col1': None, 'col2': 2},
      {'col1': 'row3 cell1', 'col2': None},
      {'col1': None, 'col2': None},
      {'col1': 'row5 cell1', 'col2': 5}
    ]
    self.assertEqual(res, json_data)

    # formatted rows (in json export mode, Null values in varchar columns become '' and numbers become strings, e.g. 123 -> '123')
    res = mb.get_card_data(card_id=1, format_rows=True)
    json_data = [
      {'col1': 'row1 cell1', 'col2': '1'},
      {'col1': '', 'col2': '2'},
      {'col1': 'row3 cell1', 'col2': None},
      {'col1': '', 'col2': None},
      {'col1': 'row5 cell1', 'col2': '5'}
    ]
    self.assertEqual(res, json_data)

    # csv
    res = mb.get_card_data(card_id=1, data_format='csv')
    csv_data = 'col1,col2\nrow1 cell1,1\n,2\nrow3 cell1,\n,\nrow5 cell1,5\n'
    self.assertEqual(res, csv_data)

    # filtered data
    res = mb.get_card_data(card_id=2, parameters=[{"type":"string/=","value":['row1 cell1', 'row3 cell1'],"target":["dimension",["template-tag","test_filter"]]}])
    filtered_data = [{'col1': 'row1 cell1', 'col2': 1}, {'col1': 'row3 cell1', 'col2': None}]
    self.assertEqual(res, filtered_data)



  def test_clone_card(self):
    # native question
    res = mb.clone_card(2, 9, 10, new_card_name='test_clone_native', new_card_collection_id=1, return_card=True)
    # simple/custom question
    res2 = mb.clone_card(3, 9, 10, new_card_name='test_clone_simple1', new_card_collection_id=1, return_card=True)
    res3 = mb.clone_card(4, 9, 10, new_card_name='test_clone_simple2', new_card_collection_id=1, return_card=True)
    
    # rewriting a value because it's not reliable
    res3['dataset_query']['query']['order-by'] = ''
    
    expected_res3_query_version1 = { 'database': 2,
                            'query': {'source-table': 10,
                                      'aggregation': [['avg', ['field', 75, None]]],
                                      'breakout': [['field', 74, None]],
                                      'order-by': ''
                                    },
                            'type': 'query'
                          }
    # we have two versions because the assigned field id is not necessarily in the order of columns as they appear in db
    expected_res3_query_version2 = { 'database': 2,
                            'query': {'source-table': 10,
                                      'aggregation': [['avg', ['field', 74, None]]],
                                      'breakout': [['field', 75, None]],
                                      'order-by': ''
                                    },
                            'type': 'query'
                          }
    
    self.assertTrue(res3['dataset_query'] == expected_res3_query_version1 or res3['dataset_query'] == expected_res3_query_version2, res3['dataset_query'])

    # add to cleanup list
    Metabase_API_Test.cleanup_objects['card'].extend([res['id'], res2['id'], res3['id']])



  def test_update_column(self):
    mb.update_column(params={'semantic_type':'type/City'}, column_id=72)
    res = mb.get('/api/field/72')['semantic_type']
    self.assertEqual(res, 'type/City')

    mb.update_column(params={'semantic_type':'type/Category'}, column_id=72)
    res = mb.get('/api/field/72')['semantic_type']
    self.assertEqual(res, 'type/Category')



if __name__ == '__main__':
  unittest.main()
