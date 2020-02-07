[![PyPI version](https://badge.fury.io/py/metabase-api.svg)](https://badge.fury.io/py/metabase-api)
[![HitCount](http://hits.dwyl.com/vvaezian/metabase_api_python.svg)](http://hits.dwyl.com/vvaezian/metabase_api_python)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg)](https://github.com/vvaezian/metabase_api_python/issues)

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

### Custom Functions
There are several custom functions such as *move_to_archive, get_collection_id, get_db_id*, .... the main custom function is the *create_card* function which is described below.  
#### `create_card` function
- Specify the name to be used for the card, which table to use as the source of data and where (i.e. which collection) to save the card (default is the root collection).  
```python
mb.create_card(card_name='test_card', table_name='mySourceTable')
```
- Using the `column_order` parameter we can specify how the order of columns should be in the created card. Accepted values are *'alphabetical', 'db_table_order'* (default), or a list of column names.
```python
mb.create_card(card_name='test_card', table_nam='mySourceTable', column_order=['myCol5', 'myCol3', 'myCol8'])
```
- All or part of the function arguments and many more information (e.g. visualisation settings) can be provided to the function in a dictionary (using the *custom_json* parameter).
```python
mb.create_card(custom_json=myCustomJson)
```
It's very helpful to use the Inspect tool of the browser (network tab) to see what Metabase is doing. You can then use the generated json code to build your automation. To turn the generated json in the browser into a Python dictionary, you can copy the code, paste it into triple quotes (`'''  '''`) and apply the function `make_json`:
```python
raw_json = ''' {"name":"test","dataset_query":{"database":165,"query":{"fields":[["field-id",35839],["field-id",35813],["field-id",35829],["field-id",35858],["field-id",35835],["field-id",35803],["field-id",35843],["field-id",35810],["field-id",35826],["field-id",35815],["field-id",35831],["field-id",35827],["field-id",35852],["field-id",35832],["field-id",35863],["field-id",35851],["field-id",35850],["field-id",35864],["field-id",35854],["field-id",35846],["field-id",35811],["field-id",35933],["field-id",35862],["field-id",35833],["field-id",35816]],"source-table":2154},"type":"query"},"display":"table","description":null,"visualization_settings":{"table.column_formatting":[{"columns":["Diff"],"type":"range","colors":["#ED6E6E","white","#84BB4C"],"min_type":"custom","max_type":"custom","min_value":-30,"max_value":30,"operator":"=","value":"","color":"#509EE3","highlight_row":false}],"table.pivot_column":"Sale_Date","table.cell_column":"SKUID"},"archived":false,"enable_embedding":false,"embedding_params":null,"collection_id":183,"collection_position":null,"result_metadata":[{"name":"Sale_Date","display_name":"Sale_Date","base_type":"type/DateTime","fingerprint":{"global":{"distinct-count":1,"nil%":0},"type":{"type/DateTime":{"earliest":"2019-12-28T00:00:00","latest":"2019-12-28T00:00:00"}}},"special_type":null},{"name":"Account_ID","display_name":"Account_ID","base_type":"type/Text","fingerprint":{"global":{"distinct-count":411,"nil%":0},"type":{"type/Text":{"percent-json":0,"percent-url":0,"percent-email":0,"average-length":9}}},"special_type":null},{"name":"Account_Name","display_name":"Account_Name","base_type":"type/Text","fingerprint":{"global":{"distinct-count":410,"nil%":0.0015},"type":{"type/Text":{"percent-json":0,"percent-url":0,"percent-email":0,"average-length":21.2916}}},"special_type":null},{"name":"Account_Type","display_name":"Account_Type","base_type":"type/Text","special_type":"type/Category","fingerprint":{"global":{"distinct-count":5,"nil%":0.0015},"type":{"type/Text":{"percent-json":0,"percent-url":0,"percent-email":0,"average-length":3.7594}}}}],"metadata_checksum":"7XP8bmR1h5f662CFE87tjQ=="} '''
myJson = mb.make_json(raw_json, prettyprint=True)
mb.create_card('test_card2', table_name='mySourceTable', custom_json={'visualization_settings':myJson['visualization_settings']})
```
For the complete list of arguments see the [definition](https://github.com/vvaezian/metabase_api_python/blob/8decd21c0e03aeb0f5d4243e081c1bc1a08d627b/metabase_api/metabase_api.py#L202) of the function.
## Notes
- There are also two other Python wrappers for Metabase API [here](https://github.com/mertsalik/metabasepy) and [here](https://github.com/STUnitas/metabase-py).
