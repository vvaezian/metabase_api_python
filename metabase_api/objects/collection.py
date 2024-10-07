import logging
from typing import Any, Callable, Optional

from metabase_api.metabase_api import Metabase_API
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
        as_json = metabase_api.get(f"/api/card/{coll_id}")
        return Collection(as_json, metabase_api=metabase_api)

    @property
    def items(self) -> list[dict[Any, Any]]:
        collection_details = self.metabase_api.get(
            f"/api/collection/{self.object_id}/items"
        )
        return list(collection_details["data"])

    def traverse(
        self,
        f: Callable[[dict[Any, Any], TraverseStack], ReturnValue],
        call_stack: Optional[TraverseStack] = None,
    ) -> ReturnValue:
        _logger.info(f"Visiting collection id '{self.object_id}'")
        if call_stack is None:
            call_stack = TraverseStack()
        r: ReturnValue = ReturnValue.empty()
        for item in self.items:
            if item["model"] == "card":
                with call_stack.add(TraverseStackElement.CARD):
                    r = r.union(f(self.as_json, call_stack))
            elif item["model"] == "collection":
                with call_stack.add(TraverseStackElement.COLLECTION):
                    r = r.union(f(self.as_json, call_stack))
            elif item["model"] == "dashboard":
                with call_stack.add(TraverseStackElement.DASHBOARD):
                    r = r.union(f(self.as_json, call_stack))
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
