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



    async def clone_card(self, card_id, 
                        source_table_id=None, target_table_id=None, 
                        source_table_name=None, target_table_name=None, 
                        new_card_name=None, new_card_collection_id=None, 
                        ignore_these_filters=None, return_card=False):
        """
        Async version of clone_card.
        """
        if not source_table_id:
            if not source_table_name:
                raise ValueError('Either the name or id of the source table needs to be provided.')
            else:
                source_table_id = await self.get_item_id('table', source_table_name)

        if not target_table_id:
            if not target_table_name:
                raise ValueError('Either the name or id of the target table needs to be provided.')
            else:
                target_table_id = await self.get_item_id('table', target_table_name)

        if ignore_these_filters:
            assert type(ignore_these_filters) == list 

        card_info = await self.get_item_info('card', card_id)
        target_table_col_name_id_mapping = await self.get_columns_name_id(table_id=target_table_id)
        source_table_col_id_name_mapping = await self.get_columns_name_id(table_id=source_table_id, column_id_name=True)

        if card_info['dataset_query']['type'] == 'native':
            filters_data = card_info['dataset_query']['native']['template-tags']
            if not source_table_name:
                source_table_name = await self.get_item_name('table', source_table_id)
            if not target_table_name:
                target_table_name = await self.get_item_name('table', target_table_id)
            card_info['dataset_query']['native']['query'] = card_info['dataset_query']['native']['query'].replace(source_table_name, target_table_name)
            for filter_variable_name, data in filters_data.items():
                if ignore_these_filters is not None and filter_variable_name in ignore_these_filters:
                    continue
                column_id = data['dimension'][1]
                column_name = source_table_col_id_name_mapping[column_id]
                target_col_id = target_table_col_name_id_mapping[column_name]
                card_info['dataset_query']['native']['template-tags'][filter_variable_name]['dimension'][1] = target_col_id

        elif card_info['dataset_query']['type'] == 'query':
            query_data = card_info['dataset_query']['query']
            query_data['source-table'] = target_table_id
            query_data_str = str(query_data)
            import re
            res = re.findall(r"\['field', .*?\]", query_data_str)
            source_column_IDs = [ eval(i)[1] for i in res ]
            for source_col_id in source_column_IDs:
                source_col_name = source_table_col_id_name_mapping[source_col_id]
                target_col_id = target_table_col_name_id_mapping[source_col_name]
                query_data_str = query_data_str.replace("['field', {}, ".format(source_col_id), "['field', {}, ".format(target_col_id))
            card_info['dataset_query']['query'] = eval(query_data_str)

        new_card_json = {}
        for key in ['dataset_query', 'display', 'visualization_settings']:
            new_card_json[key] = card_info[key]

        if new_card_name:
            new_card_json['name'] = new_card_name
        else:
            new_card_json['name'] = card_info['name']

        if new_card_collection_id:
            new_card_json['collection_id'] = new_card_collection_id
        else:
            new_card_json['collection_id'] = card_info['collection_id']

        if return_card:
            return await self.create_card(custom_json=new_card_json, verbose=True, return_card=return_card)
        else:
            await self.create_card(custom_json=new_card_json, verbose=True)



    async def move_to_archive(self, item_type, item_name=None, item_id=None, 
                              collection_name=None, collection_id=None, table_id=None, verbose=False):
        '''
        Async version of move_to_archive.
        '''
        assert item_type in ['card', 'dashboard', 'collection', 'pulse', 'segment']

        if not item_id:
            if not item_name:
                raise ValueError('Either the name or id of the {} must be provided.'.format(item_type))
            if item_type == 'collection':
                item_id = await self.get_item_id('collection', item_name)
            elif item_type == 'segment':
                item_id = await self.get_item_id('segment', item_name, table_id=table_id)
            else:
                item_id = await self.get_item_id(item_type, item_name, collection_id, collection_name)

        if item_type == 'segment':
            res = await self.put('/api/{}/{}'.format(item_type, item_id), json={'archived':True, 'revision_message':'archived!'})
        else:
            res = await self.put('/api/{}/{}'.format(item_type, item_id), json={'archived':True})

        if res in [200, 202]:
            await self.verbose_print(verbose, 'Successfully Archived.')    
        else: 
            print('Archiving Failed.')

        return res



    async def delete_item(self, item_type, item_name=None, item_id=None, 
                         collection_name=None, collection_id=None, verbose=False):
        '''
        Async version of delete_item.
        '''
        assert item_type in ['card', 'dashboard', 'pulse']
        if not item_id:
            if not item_name:
                raise ValueError('Either the name or id of the {} must be provided.'.format(item_type))
            item_id = await self.get_item_id(item_type, item_name, collection_id, collection_name)

        return await self.delete('/api/{}/{}'.format(item_type, item_id))



    async def update_column(self, params, column_id=None, column_name=None, 
                            table_id=None, table_name=None, db_id=None, db_name=None):
        '''
        Async version of update_column.
        '''
        assert type(params) == dict

        if not column_id:
            if not column_name:
                raise ValueError('Either the name or id of the column needs to be provided.')

            if not table_id:
                if not table_name:
                    raise ValueError('When column_id is not given, either the name or id of the table needs to be provided.')
                table_id = await self.get_item_id('table', table_name, db_id=db_id, db_name=db_name)

            columns_name_id_mapping = await self.get_columns_name_id(table_name=table_name, table_id=table_id, db_name=db_name, db_id=db_id)
            column_id = columns_name_id_mapping.get(column_name)
            if column_id is None:
                raise ValueError('There is no column named {} in the provided table'.format(column_name))

        res_status_code = await self.put('/api/field/{}'.format(column_id), json=params)
        if res_status_code != 200:
            print('Column Update Failed.')

        return res_status_code



    async def add_card_to_dashboard(self, card_id, dashboard_id):
        params = {
            'cardId': card_id
        }
        await self.post(f'/api/dashboard/{dashboard_id}/cards', json=params)

    @staticmethod
    async def make_json(raw_json, prettyprint=False):
        """Async version of make_json."""
        import json
        ret_dict = json.loads(raw_json)
        if prettyprint:
            import pprint
            pprint.pprint(ret_dict)
        return ret_dict
