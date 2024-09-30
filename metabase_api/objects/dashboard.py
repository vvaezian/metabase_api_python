import logging
from dataclasses import dataclass

from metabase_api.objects.card import Card
from metabase_api.objects.defs import CollectionObject

_logger = logging.getLogger(__name__)


@dataclass(init=False)
class Dashboard(CollectionObject):

    as_json: dict

    def __init__(self, as_json: dict):
        self.as_json = as_json
        self._labels: set[str] = set()
        super().__init__()

    @property
    def labels(self) -> set[str]:
        if len(self._labels) == 0:
            dash = self.as_json
            for card_json in self.as_json.get("dashcards", list()):
                self._labels = self._labels.union(Card(card_json).labels)
            for k, v in dash.items():
                if k == "description":
                    if dash["description"] is not None:
                        self._labels.add(dash["description"])
                elif k == "tabs":
                    # tabs in dashboard
                    tabs = v
                    for a_tab in tabs:
                        # let's translate the name
                        self._labels.add(a_tab["name"])
                elif k == "parameters":
                    parameters = v
                    for params_dict in parameters:
                        # let's translate the name
                        self._labels.add(params_dict["name"])
                # elif k == "name":
                #     # change name, tag it, and go!
                #     dash["name"] = (
                #         new_dashboard_name
                #         if new_dashboard_name is not None
                #         else dash["name"]
                #     )
                elif k == "description":
                    if (dash["description"] is not None) and (
                        dash["description"] != ""
                    ):
                        self._labels.add(dash["description"])
        return self.clean_labels(self._labels)
