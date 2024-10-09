import logging
from typing import Any, Callable, Optional

from metabase_api.metabase_api import Metabase_API
from metabase_api.objects.card import Card
from metabase_api.objects.dashboard import Dashboard
from metabase_api.objects.defs import (
    CollectionObject,
    TraverseStack,
    ReturnValue,
    TraverseStackElement,
    MigrationParameters,
)

_logger = logging.getLogger(__name__)


class Collection(CollectionObject):

    as_json: dict[Any, Any]

    def __init__(self, as_json: dict[Any, Any], metabase_api: Metabase_API):
        self.metabase_api = metabase_api
        super().__init__(as_json=as_json)

    @classmethod
    def from_id(cls, coll_id: int, metabase_api: Metabase_API) -> "Collection":
        as_json = metabase_api.get(f"/api/card/{coll_id}")
        return Collection(as_json, metabase_api=metabase_api)

    @property
    def items(self) -> list[dict[Any, Any]]:
        collection_details = self.metabase_api.get(
            f"/api/collection/{self.object_id}/items"
        )
        return list(collection_details["data"])

    def migrate_orig(self, params: MigrationParameters, push: bool) -> bool:
        """[Overrides from 'object'] Migrates the object, based on a set of parameters. Pushes if flag is True."""
        # get all collection items
        dst_collection_id = self.object_id
        collections_ids_to_visit: list[int] = [dst_collection_id]
        items: list[dict[Any, Any]] = []
        while len(collections_ids_to_visit) > 0:
            coll_id = collections_ids_to_visit[0]
            collections_ids_to_visit = collections_ids_to_visit[1:]
            collection_details = self.metabase_api.get(
                f"/api/collection/{coll_id}/items"
            )
            collection_items = collection_details["data"]
            # are there sub-collections in this collection?
            if "collection" in collection_details["models"]:
                # we need to collect the items recursively
                sub_collections = [
                    item["id"]
                    for item in collection_items
                    if item["model"] == "collection"
                ]
                collections_ids_to_visit = collections_ids_to_visit + sub_collections
            # I won't need to visit the collections themselves anymore:
            items = items + [
                item for item in collection_items if item["model"] != "collection"
            ]

        card_items = [item for item in items if item["model"] == "card"]
        for item in card_items:
            # nb: I can't do this
            # r = Card(card_json=item).migrate(card_params)
            # because not _all_ info is there. Need to fetch it again:
            _card = Card.from_id(card_id=item["id"], metabase_api=self.metabase_api)
            if not _card.migrate(params=params, push=False):
                raise RuntimeError(f"Impossible to migrate card '{item['id']}'")
            if not _card.push(self.metabase_api):
                raise RuntimeError(f"Impossible to push card '{item['id']}'")
        # and now we migrate dashboards
        dashboard_items = [item for item in items if item["model"] == "dashboard"]
        # todo: WHY was I checking this condition below if then I wasn't assigning it anywhere?
        # if (len(dashboard_items) == 0) and (new_dashboard_description is not None):
        #     _logger.warning(
        #         f"Dashboard description specified ('{new_dashboard_description}') but no dashboard present in the collection."
        #     )
        for item in dashboard_items:
            dashboard_id = item["id"]
            _logger.info(f"Obtaining details of dashboard {dashboard_id}...")
            dash = self.metabase_api.get(f"/api/dashboard/{dashboard_id}")
            if dash["archived"]:
                _logger.info(
                    f"Dashboard {dashboard_id} is archived. Will migrate anyways."
                )
            _logger.info(f"Migrating dashboard {dashboard_id}...")
            dashboard = Dashboard(dash)
            dashboard.migrate(params=params, push=False)
            # if len(params.personalization_options.labels_replacements) > 0:
            #     _logger.info(f"Replacing dashboard {dashboard_id}'s labels ...")
            #     dashboard.translate(
            #         translation_dict=params.personalization_options.labels_replacements
            #     )
            assert dashboard.push(
                self.metabase_api
            ), f"Problems updating dashboard '{dashboard_id}'"
        return True

    def traverse(
        self,
        f: Callable[[dict[Any, Any], TraverseStack], ReturnValue],
        call_stack: Optional[TraverseStack] = None,
    ) -> ReturnValue:
        _logger.info(f"Visiting collection id '{self.object_id}'")
        if call_stack is None:
            call_stack = TraverseStack()
        r: ReturnValue = ReturnValue.empty()
        with call_stack.add(TraverseStackElement.COLLECTION):
            r = r.union(f(self.as_json, call_stack))
            for item in self.items:
                if item["model"] == "card":
                    # nb: I can't do this
                    # r = Card(card_json=item).migrate(card_params)
                    # because not _all_ info is there. Need to fetch it again:
                    _card = Card.from_id(
                        card_id=item["id"], metabase_api=self.metabase_api
                    )
                    r = r.union(_card.traverse(f, call_stack))
                    if not _card.push(self.metabase_api):
                        raise RuntimeError(f"Impossible to push card '{item['id']}'")
                elif (
                    item["model"] == "collection"
                ):  # todo: do I need to go depth-first...?
                    r = r.union(
                        Collection.from_id(
                            coll_id=item["id"], metabase_api=self.metabase_api
                        ).traverse(f, call_stack)
                    )
                elif item["model"] == "dashboard":
                    # Dashboard(as_json=item)
                    dashboard_id = item["id"]
                    _logger.info(f"Obtaining details of dashboard {dashboard_id}...")
                    dash = self.metabase_api.get(f"/api/dashboard/{dashboard_id}")
                    if dash["archived"]:
                        _logger.info(
                            f"Dashboard {dashboard_id} is archived. Will migrate anyways."
                        )
                    _logger.info(f"Migrating dashboard {dashboard_id}...")
                    _dashboard = Dashboard(dash)
                    r = r.union(_dashboard.traverse(f, call_stack))
                    assert _dashboard.push(
                        self.metabase_api
                    ), f"Problems updating dashboard '{dashboard_id}'"
                # copy a pulse
                elif item["model"] == "pulse":
                    with call_stack.add(TraverseStackElement.PULSE):
                        r = r.union(f(self.as_json, call_stack))
                else:
                    raise ValueError(
                        f"We are not copying objects of type '{item['model']}'; specifically the one named '{item['name']}'!!!"
                    )
        return r

    def push(self, metabase_api: Metabase_API) -> bool:
        raise NotImplementedError()
