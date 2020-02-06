### Installation
```python
pip install metabase-api
```

### Initializing
```python
from metabase_api import Metabase_API

mb = Metabase_API('https://...', 'myUserName')  # if password is not given it will prompt for password
```
Calling Metabase API endpoints (documented [here](https://github.com/metabase/metabase/blob/master/docs/api-documentation.md)) can be done using the corresponding function in the Python wrapper.  
E.g. to call the [endpoint](https://github.com/metabase/metabase/blob/master/docs/api-documentation.md#get-apidatabase) `GET /api/database/`, use `mb.get('/api/database/')`.

There are also two other Python wrappers for Metabase API [here](https://github.com/mertsalik/metabasepy) and [here](https://github.com/STUnitas/metabase-py).
