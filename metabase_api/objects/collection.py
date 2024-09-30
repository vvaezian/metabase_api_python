from metabase_api import Metabase_API
from metabase_api.objects.card import Card
from metabase_api.objects.dashboard import Dashboard
from metabase_api.objects.defs import CollectionObject


class Collection(CollectionObject):

    as_json: dict

    def __init__(self, as_json: dict, metabase_api: Metabase_API):
        self.as_json = as_json
        self._labels: set[str] = set()
        self.metabase_api = metabase_api
        super().__init__()

    @classmethod
    def from_id(cls, coll_id: int, metabase_api: Metabase_API) -> "Collection":
        as_json = metabase_api.get(f"/api/card/{coll_id}")
        return Collection(as_json, metabase_api=metabase_api)

    @property
    def object_id(self) -> int:
        return self.as_json["id"]

    @property
    def items(self) -> dict:
        collection_details = self.metabase_api.get(
            f"/api/collection/{self.object_id}/items"
        )
        return collection_details["data"]

    @property
    def labels(self) -> set[str]:
        """Scans the collection and returns its labels."""
        if len(self._labels) == 0:
            # scans all items of collection
            for item in self.items:
                if item["model"] == "card":
                    self._labels = self._labels.union(Card(item).labels)
                elif item["model"] == "collection":
                    self._labels = self._labels.union(
                        Collection(item, metabase_api=self.metabase_api).labels
                    )
                elif item["model"] == "dashboard":
                    self._labels = self._labels.union(Dashboard(item).labels)
                # copy a pulse
                elif item["model"] == "pulse":
                    continue
                else:
                    raise ValueError(
                        f"We are not copying objects of type '{item['model']}'; specifically the one named '{item['name']}'!!!"
                    )
        return self.clean_labels(self._labels)
