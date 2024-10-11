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
)

_logger = logging.getLogger(__name__)


class Collection(CollectionObject):

    as_json: dict[Any, Any]

    def __init__(self, as_json: dict[Any, Any], metabase_api: Metabase_API):
        self.metabase_api = metabase_api
        super().__init__(as_json=as_json)

    @classmethod
    def from_id(cls, coll_id: int, metabase_api: Metabase_API) -> "Collection":
        as_json = metabase_api.get(f"/api/collection/{coll_id}")
        return Collection(as_json, metabase_api=metabase_api)

    @property
    def items(self) -> list[dict[Any, Any]]:
        collection_details = self.metabase_api.get(
            f"/api/collection/{self.object_id}/items"
        )
        return list(collection_details["data"])

    @property
    def dashboard_name_and_id(self) -> tuple[str, int]:
        """Expects only 1 dashboard!"""
        for i in self.items:
            if i["model"] == "dashboard":
                return i["name"], i["id"]
        raise ValueError(
            f"Collection '{self.object_id}' does not seem to have a dashboard"
        )

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
