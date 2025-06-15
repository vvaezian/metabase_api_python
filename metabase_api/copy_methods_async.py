
async def copy_card(self, source_card_name=None, source_card_id=None, 
                source_collection_name=None, source_collection_id=None,
                destination_card_name=None, 
                destination_collection_name=None, destination_collection_id=None,
                postfix='', verbose=False, return_card=False):
    """
    Async version of copy_card.
    Copy the card with the given name/id to the given destination collection.
    """
    # Making sure we have the data that we need 
    if not source_card_id:
        if not source_card_name:
            raise ValueError('Either the name or id of the source card must be provided.')
        else:
            source_card_id = await self.get_item_id(item_type='card',
                                              item_name=source_card_name, 
                                              collection_id=source_collection_id, 
                                              collection_name=source_collection_name)

    if not destination_collection_id:
        if not destination_collection_name:
            raise ValueError('Either the name or id of the destination collection must be provided.')
        else:
            destination_collection_id = await self.get_item_id('collection', destination_collection_name)

    if not destination_card_name:
        if not source_card_name:
            source_card_name = await self.get_item_name(item_type='card', item_id=source_card_id)
        destination_card_name = source_card_name + postfix

    # Get the source card info
    source_card = await self.get(f'/api/card/{source_card_id}')

    # Update the name and collection_id
    card_json = source_card
    card_json['collection_id'] = destination_collection_id
    card_json['name'] = destination_card_name

    # Fix the issue #10
    if card_json.get('description') == '': 
        card_json['description'] = None

    # Save as a new card
    res = await self.create_card(custom_json=card_json, verbose=verbose, return_card=True)

    return res if return_card else res['id']


async def copy_pulse(self, source_pulse_name=None, source_pulse_id=None, 
                source_collection_name=None, source_collection_id=None,
                destination_pulse_name=None, 
                destination_collection_id=None, destination_collection_name=None, postfix=''):
    """
    Async version of copy_pulse.
    Copy the pulse with the given name/id to the given destination collection.
    """
    # Making sure we have the data that we need 
    if not source_pulse_id:
        if not source_pulse_name:
            raise ValueError('Either the name or id of the source pulse must be provided.')
        else:
            source_pulse_id = await self.get_item_id(item_type='pulse', item_name=source_pulse_name, 
                                               collection_id=source_collection_id, 
                                               collection_name=source_collection_name)

    if not destination_collection_id:
        if not destination_collection_name:
            raise ValueError('Either the name or id of the destination collection must be provided.')
        else:
            destination_collection_id = await self.get_item_id('collection', destination_collection_name)

    if not destination_pulse_name:
        if not source_pulse_name:
            source_pulse_name = await self.get_item_name(item_type='pulse', item_id=source_pulse_id)
        destination_pulse_name = source_pulse_name + postfix

    # Get the source pulse info
    source_pulse = await self.get(f'/api/pulse/{source_pulse_id}')

    # Update the name and collection_id
    pulse_json = source_pulse
    pulse_json['collection_id'] = destination_collection_id
    pulse_json['name'] = destination_pulse_name

    # Save as a new pulse
    await self.post('/api/pulse', json=pulse_json)


async def copy_dashboard(self, source_dashboard_name=None, source_dashboard_id=None, 
                    source_collection_name=None, source_collection_id=None,
                    destination_dashboard_name=None, 
                    destination_collection_name=None, destination_collection_id=None,
                    deepcopy=False, postfix='', collection_position=1, description=''):
    """
    Async version of copy_dashboard.
    Copy the dashboard with the given name/id to the given destination collection.
    """
    # Making sure we have the data that we need 
    if not source_dashboard_id:
        if not source_dashboard_name:
            raise ValueError('Either the name or id of the source dashboard must be provided.')
        else:
            source_dashboard_id = await self.get_item_id(item_type='dashboard', item_name=source_dashboard_name, 
                                                  collection_id=source_collection_id, 
                                                  collection_name=source_collection_name)

    if not destination_collection_id:
        if not destination_collection_name:
            raise ValueError('Either the name or id of the destination collection must be provided.')
        else:
            destination_collection_id = await self.get_item_id('collection', destination_collection_name)

    if not destination_dashboard_name:
        if not source_dashboard_name:
            source_dashboard_name = await self.get_item_name(item_type='dashboard', item_id=source_dashboard_id)
        destination_dashboard_name = source_dashboard_name + postfix

    parameters = {
        'collection_id': destination_collection_id, 
        'name': destination_dashboard_name, 
        'is_deep_copy': deepcopy,
        'collection_position': collection_position,
        'description': description
    }
    
    res = await self.post(f'/api/dashboard/{source_dashboard_id}/copy', 'raw', json=parameters)
    if res.status != 200:
        raise ValueError(f'Error copying the dashboard: {await res.text()}')
    
    data = await res.json()
    dup_dashboard_id = data['id']
    return dup_dashboard_id


async def copy_collection(self, source_collection_name=None, source_collection_id=None, 
                    destination_collection_name=None,
                    destination_parent_collection_name=None, destination_parent_collection_id=None, 
                    deepcopy_dashboards=False, postfix='', child_items_postfix='', verbose=False):
    """
    Async version of copy_collection.
    Copy the collection with the given name/id into the given destination parent collection.
    """
    # Making sure we have the data that we need 
    if not source_collection_id:
        if not source_collection_name:
            raise ValueError('Either the name or id of the source collection must be provided.')
        else:
            source_collection_id = await self.get_item_id('collection', source_collection_name)

    if not destination_parent_collection_id:
        if not destination_parent_collection_name:
            raise ValueError('Either the name or id of the destination parent collection must be provided.')
        else:
            destination_parent_collection_id = (
                await self.get_item_id('collection', destination_parent_collection_name)
                if destination_parent_collection_name != 'Root'
                else None
            )

    if not destination_collection_name:
        if not source_collection_name:
            source_collection_name = await self.get_item_name(item_type='collection', item_id=source_collection_id)
        destination_collection_name = source_collection_name + postfix

    # Create a collection in the destination to hold the contents of the source collection
    res = await self.create_collection(
        destination_collection_name, 
        parent_collection_id=destination_parent_collection_id, 
        parent_collection_name=destination_parent_collection_name,
        return_results=True
    )
    destination_collection_id = res['id']    

    # Get the items to copy
    items = await self.get(f'/api/collection/{source_collection_id}/items')
    if type(items) == dict:  # in Metabase version *.40.0 the format of the returned result for this endpoint changed
        items = items['data']

    # Copy the items of the source collection to the new collection
    for item in items:
        # Copy a collection
        if item['model'] == 'collection':
            collection_id = item['id']
            collection_name = item['name'] 
            destination_collection_name = collection_name + child_items_postfix
            self.verbose_print(verbose, f'Copying the collection "{collection_name}" ...')
            await self.copy_collection(
                source_collection_id=collection_id,
                destination_parent_collection_id=destination_collection_id,
                child_items_postfix=child_items_postfix,
                deepcopy_dashboards=deepcopy_dashboards,
                verbose=verbose
            )

        # Copy a dashboard
        if item['model'] == 'dashboard':
            dashboard_id = item['id']
            dashboard_name = item['name']
            destination_dashboard_name = dashboard_name + child_items_postfix
            self.verbose_print(verbose, f'Copying the dashboard "{dashboard_name}" ...')
            await self.copy_dashboard(
                source_dashboard_id=dashboard_id,
                destination_collection_id=destination_collection_id,
                destination_dashboard_name=destination_dashboard_name,
                deepcopy=deepcopy_dashboards
            )

        # Copy a card
        if item['model'] == 'card':
            card_id = item['id']
            card_name = item['name']
            destination_card_name = card_name + child_items_postfix
            self.verbose_print(verbose, f'Copying the card "{card_name}" ...')
            await self.copy_card(
                source_card_id=card_id,
                destination_collection_id=destination_collection_id,
                destination_card_name=destination_card_name
            )

        # Copy a pulse
        if item['model'] == 'pulse':
            pulse_id = item['id']
            pulse_name = item['name']
            destination_pulse_name = pulse_name + child_items_postfix
            self.verbose_print(verbose, f'Copying the pulse "{pulse_name}" ...')
            await self.copy_pulse(
                source_pulse_id=pulse_id,
                destination_collection_id=destination_collection_id,
                destination_pulse_name=destination_pulse_name
            )
