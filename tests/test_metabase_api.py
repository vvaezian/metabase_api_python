import unittest
from metabase_api import Metabase_API
import datetime

LOGIN_DOMAIN = os.environ.get("LOGIN_DOMAIN")
LOGIN_EMAIL = os.environ.get("LOGIN_USERNAME")
LOGIN_PASSWORD = os.environ.get("LOGIN_PASSWORD")

mb = Metabase_API(LOGIN_DOMAIN, LOGIN_EMAIL, LOGIN_PASSWORD)


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
      



  ### Helper Functions
  def test_get_item_info(self):
    # database
    res = mb.get_item_info('database', 5)
    self.assertEqual(res['name'], 'test_db')
    self.assertEqual(res['id'], 5)

    # table
    res = mb.get_item_info('table', 101)
    self.assertEqual(res['name'], 'test_table')
    self.assertEqual(res['id'], 101)

    # card
    res = mb.get_item_info('card', 166)
    self.assertEqual(res['name'], 'test_card')
    self.assertEqual(res['id'], 166)

    # collection
    res = mb.get_item_info('collection', 28)
    self.assertEqual(res['name'], 'test_collection')
    self.assertEqual(res['id'], 28)

    # dashboard
    res = mb.get_item_info('dashboard', 35)
    self.assertEqual(res['name'], 'test_dashboard')
    self.assertEqual(res['id'], 35)

    # segment'
    res = mb.get_item_info('segment', 18)
    self.assertEqual(res['name'], 'test_segment')
    self.assertEqual(res['id'], 18)

    # pulse



  def test_get_item_name(self):
    # database
    db_id = mb.get_item_name('database', 5)
    self.assertEqual(db_id, 'test_db')

    # table
    table_id = mb.get_item_name('table', 101)
    self.assertEqual(table_id, 'test_table')

    # card
    card_id = mb.get_item_name('card', 166)
    self.assertEqual(card_id, 'test_card')

    # collection
    collection_id = mb.get_item_name('collection', 28)
    self.assertEqual(collection_id, 'test_collection')

    # dashboard
    dashboard_id = mb.get_item_name('dashboard', 35)
    self.assertEqual(dashboard_id, 'test_dashboard')

    # segment'
    segment_id = mb.get_item_name('segment', 18)
    self.assertEqual(segment_id, 'test_segment')

    # pulse



  def test_get_item_id(self):
    # database
    db_name = mb.get_item_id('database', 'test_db')
    self.assertEqual(db_name, 5)

    # table
    table_name = mb.get_item_id('table', 'test_table')
    self.assertEqual(table_name, 101)

    # card
    card_name = mb.get_item_id('card', 'test_card')
    self.assertEqual(card_name, 166)

    # collection
    collection_name = mb.get_item_id('collection', 'test_collection')
    self.assertEqual(collection_name, 28)

    with self.assertRaises(ValueError) as error:
      mb.get_item_id('collection', 'test_collection_dup')  
    self.assertEqual(str(error.exception), 'There is more than one collection with the name "test_collection_dup"')

    with self.assertRaises(ValueError) as error:
      mb.get_item_id('collection', 'xyz')  
    self.assertEqual(str(error.exception), 'There is no collection with the name "xyz"')

    # dashboard
    dashboard_name = mb.get_item_id('dashboard', 'test_dashboard')
    self.assertEqual(dashboard_name, 35)

    # pulse

    # segment
    segment_name = mb.get_item_id('segment', 'test_segment')
    self.assertEqual(segment_name, 18)

    
    

if __name__ == '__main__':
  unittest.main()
