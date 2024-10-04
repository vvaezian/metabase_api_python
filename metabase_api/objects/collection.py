from typing import Any, Callable, Optional

from metabase_api.metabase_api import Metabase_API
from metabase_api.objects.defs import (
    CollectionObject,
    TraverseStack,
    ReturnValue,
    CardParameters,
)


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
    def object_id(self) -> int:
        return int(self.as_json["id"])

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
        raise NotImplementedError()

    def migrate(self, params: CardParameters, push: bool) -> bool:
        raise NotImplementedError()

    def push(self, metabase_api: Metabase_API) -> bool:
        raise NotImplementedError()

    # @property
    # def labels(self) -> set[str]:
    #     """Scans the collection and returns its labels."""
    #     if len(self._labels) == 0:
    #         # scans all items of collection
    #         for item in self.items:
    #             if item["model"] == "card":
    #                 self._labels = self._labels.union(Card(item).labels)
    #             elif item["model"] == "collection":
    #                 self._labels = self._labels.union(
    #                     Collection(item, metabase_api=self.metabase_api).labels
    #                 )
    #             elif item["model"] == "dashboard":
    #                 self._labels = self._labels.union(Dashboard(item).labels)
    #             # copy a pulse
    #             elif item["model"] == "pulse":
    #                 continue
    #             else:
    #                 raise ValueError(
    #                     f"We are not copying objects of type '{item['model']}'; specifically the one named '{item['name']}'!!!"
    #                 )
    #     return clean_labels(self._labels)
