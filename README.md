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
There are several custom functions such as *move_to_archive, get_collection_id, get_db_id*, ..., the main custom function is *create_card*.

## Notes
- There are also two other Python wrappers for Metabase API [here](https://github.com/mertsalik/metabasepy) and [here](https://github.com/STUnitas/metabase-py).
