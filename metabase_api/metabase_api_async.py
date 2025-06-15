import httpx
import getpass

class Metabase_API_Async:
    """
    Async version of the Metabase API wrapper.
    Provides asynchronous methods to interact with the Metabase API.
    """

    def __init__(self, domain, email=None, password=None, api_key=None, basic_auth=False, is_admin=True):
        assert email is not None or api_key is not None
        self.domain = domain.rstrip('/')
        self.email = email
        self.auth = None
        self.password = None
        self.session_id = None
        self.header = None
        self.is_admin = is_admin

        if email:
            self.password = getpass.getpass(prompt='Please enter your password: ') if password is None else password
            if basic_auth:
                self.auth = True  # We'll use aiohttp.BasicAuth in the request methods
            else:
                self.auth = None
        else:
            self.header = {"X-API-KEY": api_key}
        
        if not self.is_admin:
            print('''
                Ask your Metabase admin to disable "Friendly Table and Field Names" (in Admin Panel > Settings > General).
                Without this some of the functions of the current package may not work as expected.
            ''')
    
    async def authenticate_async(self):
        """Asynchronously get a Session ID"""
        conn_header = {
            'username': self.email,
            'password': self.password
        }

        auth = (self.email, self.password) if self.auth else None
        async with httpx.AsyncClient() as client:
            res = await client.post(
                self.domain + '/api/session',
                json=conn_header,
                auth=auth
            )
            if res.status_code != 200:
                raise Exception(f"Authentication failed with status {res.status_code}")

            data = res.json()
            self.session_id = data['id']
            self.header = {'X-Metabase-Session': self.session_id}

    async def validate_session_async(self):
        """Asynchronously get a new session ID if the previous one has expired"""
        if not self.email:  # Using API key
            return

        if not self.session_id:  # First request
            return await self.authenticate_async()

        auth = (self.email, self.password) if self.auth else None
        async with httpx.AsyncClient() as client:
            res = await client.get(
                self.domain + '/api/user/current',
                headers=self.header,
                auth=auth
            )
            if res.status_code == 200:
                return True
            elif res.status_code == 401:  # unauthorized
                return await self.authenticate_async()
            else:
                raise Exception(f"Session validation failed with status {res.status_code}")



    # Import async REST methods
    from ._rest_methods_async import get, post, put, delete
    # import helper functions
    from ._helper_methods_async import get_item_info, get_item_id, get_item_name, \
                                get_db_id_from_table_id, get_db_info, get_table_metadata, \
                                get_columns_name_id, friendly_names_is_disabled, verbose_print
    
    
    ##################################################################
    ###################### Custom Functions ##########################
    ##################################################################
    from .create_methods_async import create_card, create_collection, create_segment
    from .copy_methods_async import copy_card, copy_collection, copy_dashboard, copy_pulse

    async def search(self, q, item_type=None):
        """
        Async version of search function.
        Search for Metabase objects and return their basic info. 
        We can limit the search to a certain item type by providing a value for item_type keyword. 

        Parameters
        ----------
        q : search input
        item_type : to limit the search to certain item types (default:None, means no limit)
        """
        assert item_type in [None, 'card', 'dashboard', 'collection', 'table', 'pulse', 'segment', 'metric']

        res = await self.get(endpoint='/api/search/', params={'q': q})
        if type(res) == dict:  # in Metabase version *.40.0 the format of the returned result for this endpoint changed
            res = res['data']
        if item_type is not None:
            res = [item for item in res if item['model'] == item_type]

        return res

    async def get_card_data(self, card_name=None, card_id=None, collection_name=None, collection_id=None, 
                              data_format='json', parameters=None, format_rows=False):
        '''
        Async version of get_card_data.
        Run the query associated with a card and get the results.

        Parameters
        ----------
        data_format : specifies the format of the returned data:
            - 'json': every row is a dictionary of <column-header, cell> key-value pairs    
            - 'csv': the entire result is returned as a string, where rows are separated by newlines and cells with commas.
        parameters : can be used to pass filter values:
            The format is like [{"type":"category","value":["val1","val2"],"target":["dimension",["template-tag","filter_variable_name"]]}]
            See the network tab when exporting the results using the web interface to get the proper format pattern.
        format_rows : whether the returned results should be formatted or not
        '''
        assert data_format in ['json', 'csv']
        if parameters:
            assert type(parameters) == list

        if card_id is None:
            if card_name is None:
                raise ValueError('Either card_id or card_name must be provided.')
            card_id = await self.get_item_id(item_name=card_name,
                                         collection_name=collection_name,
                                         collection_id=collection_id,
                                         item_type='card')

        import json
        params_json = { 
            'parameters': json.dumps(parameters), 
            'format_rows': 'true' if format_rows else 'false' 
        }

        # get the results
        res = await self.post(f"/api/card/{card_id}/query/{data_format}", 'raw', data=params_json)

        # return the results in the requested format
        if data_format == 'json':
            text = res.text if hasattr(res, 'text') else await res.text()
            return json.loads(text)
        if data_format == 'csv':
            text = res.text if hasattr(res, 'text') else await res.text()
            return text.replace('null', '')
