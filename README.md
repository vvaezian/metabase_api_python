[![PyPI version](https://badge.fury.io/py/metabase-api.svg?)](https://badge.fury.io/py/metabase-api)
[![HitCount](http://hits.dwyl.com/vvaezian/metabase_api_python.svg)](http://hits.dwyl.com/vvaezian/metabase_api_python)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/vvaezian/metabase_api_python/issues)
[![GitHub license](https://img.shields.io/github/license/vvaezian/metabase_api_python.svg)](https://github.com/vvaezian/metabase_api_python/blob/master/LICENSE)

## Installation
```python
pip install metabase-api
```

## Initializing
```python
from metabase_api import Metabase_API

mb = Metabase_API('https://...', 'username', 'password')  # if password is not given, it will prompt for password
```
## Functions
### REST functions (get, post, put, delete)
Calling Metabase API endpoints (documented [here](https://github.com/metabase/metabase/blob/master/docs/api-documentation.md)) can be done using the corresponding REST function in the wrapper.  
E.g. to call the [endpoint](https://github.com/metabase/metabase/blob/master/docs/api-documentation.md#get-apidatabase) `GET /api/database/`, use `mb.get('/api/database/')`.

### Auxilliary Functions
You usually don't need to deal with these functions directly (e.g. [get_item_id](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L88), [get_item_name](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L76))

### Custom Functions

- [create_card](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L238)
- [create_segment](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L403)
- [copy_card](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L450)
- [copy_pulse](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L511)
- [copy_dashboard](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L563)
- [copy_collection](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L656)
- [update_column](https://github.com/vvaezian/metabase_api_python/blob/35e4ab921d9a0dcb6dafb0fc3b6d72a002d6acf7/metabase_api/metabase_api.py#L830)
- [make_json](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L827)
- [move_to_archive](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L757)
- [delete_item](https://github.com/vvaezian/metabase_api_python/blob/b2ef09cf81647cdfc9a3e461fa2eb955b529f50b/metabase_api/metabase_api.py#L786)  
*For a complete list of functions parameters see the functions definitions using the above links. Here we provide a short description:*

#### `create_card`
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
mb.create_card(custom_json=myCustomJson)
```

#### `create_segment`
Provide the name to be used for creating the segment, the name or id of the table you want to create the segment on, the column of that table to filter on and the filter values.
```python
mb.create_segment(segment_name='test_segment', table_name='user_table', column_name='user_id', column_values=[123, 456, 789])
```

#### `copy_card`
At the minimum you need to provide the name/id of the card to copy and the name/id of the collection to copy the card to.
```python
mb.copy_card(source_card_name='test_card', destination_collection_id=123)
```

#### `copy_pulse`
Similar to `copy_card` but for pulses.
```python
mb.copy_pulse(source_pulse_name='test_pulse', destination_collection_id=123)
```

#### `copy_dashboard`
You can determine whether you want to *deepcopy* the dashboard or not (default False).  
If you don't deepcopy, the duplicated dashboard will use the same cards as the original dashboard.  
When you deepcopy a dashboard, the cards of the original dashboard are duplicated and these cards are used in the duplicate dashboard.  
If the `destination_dashboard_name` parameter is not provided, the destination dashboard name will be the same as the source dashboard name (plus any `postfix` if provided).  
The duplicated cards (in case of deepcopying) are saved in a collection called `[destination_dashboard_name]'s cards` and placed in the same collection as the duplicated dashboard.
```python
mb.copy_dashboard(source_dashboard_id=123, destination_collection_id=456, deepcopy=True)
```

#### `copy_collection`
Copies all the items in the given collection (name/id) into the given `destination_parent_collection` (name/id). You can determine whether to deepcopy the dashboards.
```python
mb.copy_collection(source_collection_id=123, destination_parent_collection_id=456, deepcopy_dashboards=True, verbose=True)
```
You can also specify a postfix to be added to the names of the child items that get copied.

#### `update_colum`
Update the column in Data Model by providing the relevant parameter (list of all parameters can be found [here](https://www.metabase.com/docs/latest/api-documentation.html#put-apifieldid)).  
For example to change the column type to 'Category', we can use:
```python
mb.update_column(column_name='myCol', table_name='myTable', params={'special_type':'type/Category'})
```

#### `make_json`
It's very helpful to use the Inspect tool of the browser (network tab) to see what Metabase is doing. You can then use the generated json code to build your automation. To turn the generated json in the browser into a Python dictionary, you can copy the code, paste it into triple quotes (`'''  '''`) and apply the function `make_json`:
```python
raw_json = ''' {"name":"test","dataset_query":{"database":165,"query":{"fields":[["field-id",35839],["field-id",35813],["field-id",35829],["field-id",35858],["field-id",35835],["field-id",35803],["field-id",35843],["field-id",35810],["field-id",35826],["field-id",35815],["field-id",35831],["field-id",35827],["field-id",35852],["field-id",35832],["field-id",35863],["field-id",35851],["field-id",35850],["field-id",35864],["field-id",35854],["field-id",35846],["field-id",35811],["field-id",35933],["field-id",35862],["field-id",35833],["field-id",35816]],"source-table":2154},"type":"query"},"display":"table","description":null,"visualization_settings":{"table.column_formatting":[{"columns":["Diff"],"type":"range","colors":["#ED6E6E","white","#84BB4C"],"min_type":"custom","max_type":"custom","min_value":-30,"max_value":30,"operator":"=","value":"","color":"#509EE3","highlight_row":false}],"table.pivot_column":"Sale_Date","table.cell_column":"SKUID"},"archived":false,"enable_embedding":false,"embedding_params":null,"collection_id":183,"collection_position":null,"result_metadata":[{"name":"Sale_Date","display_name":"Sale_Date","base_type":"type/DateTime","fingerprint":{"global":{"distinct-count":1,"nil%":0},"type":{"type/DateTime":{"earliest":"2019-12-28T00:00:00","latest":"2019-12-28T00:00:00"}}},"special_type":null},{"name":"Account_ID","display_name":"Account_ID","base_type":"type/Text","fingerprint":{"global":{"distinct-count":411,"nil%":0},"type":{"type/Text":{"percent-json":0,"percent-url":0,"percent-email":0,"average-length":9}}},"special_type":null},{"name":"Account_Name","display_name":"Account_Name","base_type":"type/Text","fingerprint":{"global":{"distinct-count":410,"nil%":0.0015},"type":{"type/Text":{"percent-json":0,"percent-url":0,"percent-email":0,"average-length":21.2916}}},"special_type":null},{"name":"Account_Type","display_name":"Account_Type","base_type":"type/Text","special_type":"type/Category","fingerprint":{"global":{"distinct-count":5,"nil%":0.0015},"type":{"type/Text":{"percent-json":0,"percent-url":0,"percent-email":0,"average-length":3.7594}}}}],"metadata_checksum":"7XP8bmR1h5f662CFE87tjQ=="} '''
myJson = mb.make_json(raw_json)  # setting 'prettyprint=True' will print the output in a structured format.
mb.create_card('test_card2', table_name='mySourceTable', custom_json={'visualization_settings':myJson['visualization_settings']})
```

#### `move_to_archive`
Moves the item (Card, Dashboard, Collection, Pulse, Segment) to the Archive section.
```python
mb.move_to_archive('card', item_id=123)
```
#### `delete_item`
Deletes the item (Card, Dashboard, Pulse). Currently Collections and Segments cannot be deleted using the Metabase API.
```python
mb.delete_item('card', item_id=123)
```

## Notes
There are also two other Python wrappers for Metabase API [here](https://github.com/mertsalik/metabasepy) and [here](https://github.com/STUnitas/metabase-py).
