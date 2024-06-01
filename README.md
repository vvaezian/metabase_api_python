<!--[![HitCount](http://hits.dwyl.com/vvaezian/metabase_api_python.svg)](http://hits.dwyl.com/vvaezian/metabase_api_python)-->
[![PyPI version](https://badge.fury.io/py/metabase-api.svg?)](https://badge.fury.io/py/metabase-api)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/vvaezian/metabase_api_python/issues)
[![codecov](https://codecov.io/gh/vvaezian/metabase_api_python/branch/master/graph/badge.svg?token=FNH20CUC4F)](https://codecov.io/gh/vvaezian/metabase_api_python)
[![GitHub license](https://img.shields.io/github/license/vvaezian/metabase_api_python.svg)](https://github.com/vvaezian/metabase_api_python/blob/master/LICENSE)

## Installation
```python
pip install metabase-api
```

## Initializing
```python
from metabase_api import Metabase_API

# authentication using username/password
mb = Metabase_API('https://...', 'username', 'password')  # if password is not given, it will prompt for password

# authentication using API key
mb = Metabase_API('https://...', api_key='YOUR_API_KEY')
```
## Functions
### REST functions (get, post, put, delete)
Calling Metabase API endpoints (documented [here](https://github.com/metabase/metabase/blob/master/docs/api-documentation.md)) can be done using the corresponding REST function in the wrapper.  
E.g. to call the [endpoint](https://github.com/metabase/metabase/blob/master/docs/api-documentation.md#get-apidatabase) `GET /api/database/`, use `mb.get('/api/database/')`.

### Helper Functions
You usually don't need to deal with these functions directly (e.g. [get_item_info](https://github.com/vvaezian/metabase_api_python/blob/77ef837972bc169f96a3ca520da769e0b933e8a8/metabase_api/metabase_api.py#L89), [get_item_id](https://github.com/vvaezian/metabase_api_python/blob/77ef837972bc169f96a3ca520da769e0b933e8a8/metabase_api/metabase_api.py#L128), [get_item_name](https://github.com/vvaezian/metabase_api_python/blob/77ef837972bc169f96a3ca520da769e0b933e8a8/metabase_api/metabase_api.py#L116))

### Custom Functions

- [create_card](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L289)
- [create_collection](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L461)
- [create_segment](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L486)
- [copy_card](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L530)
- [copy_pulse](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L591)
- [copy_dashboard](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L643)
- [copy_collection](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L736)
- [clone_card](https://github.com/vvaezian/metabase_api_python/blob/77ef837972bc169f96a3ca520da769e0b933e8a8/metabase_api/metabase_api.py#L1003)
- [update_column](https://github.com/vvaezian/metabase_api_python/blob/77ef837972bc169f96a3ca520da769e0b933e8a8/metabase_api/metabase_api.py#L1146)
- [search](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L835)
- [get_card_data](https://github.com/vvaezian/metabase_api_python/blob/77ef837972bc169f96a3ca520da769e0b933e8a8/metabase_api/metabase_api.py#L966)
- [move_to_archive](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L933)
- [delete_item](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L963)  
- [make_json](https://github.com/vvaezian/metabase_api_python/blob/150c8143bf3ec964568d54bddd80bf9c1b2ca214/metabase_api/metabase_api.py#L1015)

*For a complete list of functions parameters see the functions definitions using the above links. Here we provide a short description:*

- #### `create_card`
Specify the name to be used for the card, which table (name/id) to use as the source of data and where (i.e. which collection (name/id)) to save the card (default is the root collection).  
```python
mb.create_card(card_name='test_card', table_name='mySourceTable')  # Setting `verbose=True` will print extra information while creating the card.
```
Using the `column_order` parameter we can specify how the order of columns should be in the created card. Accepted values are *'alphabetical', 'db_table_order'* (default), or a list of column names.
```python
mb.create_card(card_name='test_card', table_name='mySourceTable', column_order=['myCol5', 'myCol3', 'myCol8'])
```
All or part of the function parameters and many more information (e.g. visualisation settings) can be provided to the function in a dictionary, using the *custom_json* parameter. (also see the `make_json` function below)
```python
q = '''
  select *
  from my_table 
  where city = '{}'
'''

for city in city_list:

  query = q.format(city)
  
  # here I included the minimum keys required. You can add more.
  my_custom_json = {
    'name': 'test_card',
    'display': 'table',
    'dataset_query': {
      'database': db_id,
      'native': { 'query': query },
      'type': 'native' 
    }
  }
       
  # See the function definition for other parameters of the function (e.g. in which collection to save the card)
  mb.create_card(custom_json=my_custom_json)
```

- #### `create_collection`
Create an empty collection. Provide the name of the collection, and the name or id of the parent collection (i.e. where you want the created collection to reside). If you want to create the collection in the root, you need to provide `parent_collection_name='Root'`.
```python
mb.create_collection(collection_name='test_collection', parent_collection_id=123)
```

- #### `create_segment`
Provide the name to be used for creating the segment, the name or id of the table you want to create the segment on, the column of that table to filter on and the filter values.
```python
mb.create_segment(segment_name='test_segment', table_name='user_table', column_name='user_id', column_values=[123, 456, 789])
```

- #### `copy_card`
At the minimum you need to provide the name/id of the card to copy and the name/id of the collection to copy the card to.
```python
mb.copy_card(source_card_name='test_card', destination_collection_id=123)
```

- #### `copy_pulse`
Similar to `copy_card` but for pulses.
```python
mb.copy_pulse(source_pulse_name='test_pulse', destination_collection_id=123)
```

- #### `copy_dashboard`
You can determine whether you want to *deepcopy* the dashboard or not (default False).  
If you don't deepcopy, the duplicated dashboard will use the same cards as the original dashboard.  
When you deepcopy a dashboard, the cards of the original dashboard are duplicated and these cards are used in the duplicate dashboard.  
If the `destination_dashboard_name` parameter is not provided, the destination dashboard name will be the same as the source dashboard name (plus any `postfix` if provided).  
The duplicated cards (in case of deepcopying) are saved in a collection called `[destination_dashboard_name]'s cards` and placed in the same collection as the duplicated dashboard.
```python
mb.copy_dashboard(source_dashboard_id=123, destination_collection_id=456, deepcopy=True)
```

- #### `copy_collection`
Copies the given collection and its contents to the given `destination_parent_collection` (name/id). You can determine whether to deepcopy the dashboards.
```python
mb.copy_collection(source_collection_id=123, destination_parent_collection_id=456, deepcopy_dashboards=True, verbose=True)
```
You can also specify a postfix to be added to the names of the child items that get copied.

- #### `clone_card`
Similar to `copy_card` but a different table is used as the source for filters of the card.  
This comes in handy when you want to create similar cards with the same filters that differ only on the source of the filters (e.g. cards for 50 US states).
```python
mb.clone_card(card_id=123, source_table_id=456, target_table_id=789, new_card_name='test clone', new_card_collection_id=1)
```

- #### `update_column`
Update the column in Data Model by providing the relevant parameter (list of all parameters can be found [here](https://www.metabase.com/docs/latest/api-documentation.html#put-apifieldid)).  
For example to change the column type to 'Category', we can use:
```python
mb.update_column(column_name='myCol', table_name='myTable', params={'semantic_type':'type/Category'}  # (For Metabase versions before v.39, use: params={'special_type':'type/Category'}))
```

- #### `search`
Searches for Metabase objects and returns basic info.  
Provide the search term and optionally `item_type` to limit the results.
```Python
mb.search(q='test', item_type='card')
```

- #### `get_card_data`
Returns the rows.  
Provide the card name/id and the data format of the output (csv or json). You can also provide filter values.
```python
results = mb.get_card_data(card_id=123, data_format='csv')
```

- #### `make_json`
It's very helpful to use the Inspect tool of the browser (network tab) to see what Metabase is doing. You can then use the generated json code to build your automation. To turn the generated json in the browser into a Python dictionary, you can copy the code, paste it into triple quotes (`'''  '''`) and apply the function `make_json`:
```python
raw_json = ''' {"name":"test","dataset_query":{"database":165,"query":{"fields":[["field-id",35839],["field-id",35813],["field-id",35829],["field-id",35858],["field-id",35835],["field-id",35803],["field-id",35843],["field-id",35810],["field-id",35826],["field-id",35815],["field-id",35831],["field-id",35827],["field-id",35852],["field-id",35832],["field-id",35863],["field-id",35851],["field-id",35850],["field-id",35864],["field-id",35854],["field-id",35846],["field-id",35811],["field-id",35933],["field-id",35862],["field-id",35833],["field-id",35816]],"source-table":2154},"type":"query"},"display":"table","description":null,"visualization_settings":{"table.column_formatting":[{"columns":["Diff"],"type":"range","colors":["#ED6E6E","white","#84BB4C"],"min_type":"custom","max_type":"custom","min_value":-30,"max_value":30,"operator":"=","value":"","color":"#509EE3","highlight_row":false}],"table.pivot_column":"Sale_Date","table.cell_column":"SKUID"},"archived":false,"enable_embedding":false,"embedding_params":null,"collection_id":183,"collection_position":null,"result_metadata":[{"name":"Sale_Date","display_name":"Sale_Date","base_type":"type/DateTime","fingerprint":{"global":{"distinct-count":1,"nil%":0},"type":{"type/DateTime":{"earliest":"2019-12-28T00:00:00","latest":"2019-12-28T00:00:00"}}},"special_type":null},{"name":"Account_ID","display_name":"Account_ID","base_type":"type/Text","fingerprint":{"global":{"distinct-count":411,"nil%":0},"type":{"type/Text":{"percent-json":0,"percent-url":0,"percent-email":0,"average-length":9}}},"special_type":null},{"name":"Account_Name","display_name":"Account_Name","base_type":"type/Text","fingerprint":{"global":{"distinct-count":410,"nil%":0.0015},"type":{"type/Text":{"percent-json":0,"percent-url":0,"percent-email":0,"average-length":21.2916}}},"special_type":null},{"name":"Account_Type","display_name":"Account_Type","base_type":"type/Text","special_type":"type/Category","fingerprint":{"global":{"distinct-count":5,"nil%":0.0015},"type":{"type/Text":{"percent-json":0,"percent-url":0,"percent-email":0,"average-length":3.7594}}}}],"metadata_checksum":"7XP8bmR1h5f662CFE87tjQ=="} '''
myJson = mb.make_json(raw_json)  # setting 'prettyprint=True' will print the output in a structured format.
mb.create_card('test_card2', table_name='mySourceTable', custom_json={'visualization_settings':myJson['visualization_settings']})
```

- #### `move_to_archive`
Moves the item (Card, Dashboard, Collection, Pulse, Segment) to the Archive section.
```python
mb.move_to_archive('card', item_id=123)
```
- #### `delete_item`
Deletes the item (Card, Dashboard, Pulse). Currently Collections and Segments cannot be deleted using the Metabase API.
```python
mb.delete_item('card', item_id=123)
```
