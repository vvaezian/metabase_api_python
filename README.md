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
There are several custom functions such as *move_to_archive, get_collection_id, get_db_id*, .... the main custom function is the *create_card* function.  
#### `create_card` function
- We need to provide a name for the card, tell the function which table to use as the source of data and optionally say in which collection to save the card (if no collection is given the card is saved in the root collection).  
```python
mb.create_card(card_name='test_card', table_nam='mySourceTable')
```
- All or part of the function arguments and many more information (e.g. visualisation settings) can be provided to the function in a dictionary (using the *custom_json* parameter).
```python
mb.create_card(custom_json=myCustomJson)
```
- Using the `column_order` parameter we can specify how the order of columns should be in the created card. Accepted values are *'alphabetical', 'db_table_order'* (default), or a list of column names.
```python
mb.create_card(card_name='test_card', table_nam='mySourceTable', column_order=['myCol5', 'myCol3', 'myCol8'])
```
## Notes
- There are also two other Python wrappers for Metabase API [here](https://github.com/mertsalik/metabasepy) and [here](https://github.com/STUnitas/metabase-py).
