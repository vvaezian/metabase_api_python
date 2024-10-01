import logging
from copy import deepcopy
from dataclasses import dataclass
from typing import Callable, Optional

from metabase_api import Metabase_API
from metabase_api.objects.defs import (
    CollectionObject,
    ReturnValue,
    TraverseStackElement,
    TraverseStack,
)

MIGRATED_CARDS: list[int] = list()


_logger = logging.getLogger(__name__)


@dataclass(init=False)
class Card(CollectionObject):
    """A Card! :-)"""

    card_json: dict

    def __init__(self, card_json: dict):
        if "model" in card_json:  # field not always there. Depends on provenance.
            assert (
                card_json["model"] == "card"
            ), f"json structure does not contain a card; it contains '{card_json['model']}'"
        self.card_json = card_json
        self._labels: set[str] = set()
        super().__init__()

    @classmethod
    def from_id(cls, card_id: int, metabase_api: Metabase_API) -> "Card":
        card_json = metabase_api.get(f"/api/card/{card_id}")
        return Card(card_json=card_json)

    @property
    def card_id(self) -> int:
        return self.card_json["id"]

    def _label_fetcher(
        self, caller_json: dict, call_stack: TraverseStack
    ) -> ReturnValue:
        """Fetches labels from a structure."""
        if call_stack.empty:
            raise RuntimeError("Call stack is empty - this shouldn't happen!")
        top_of_stack = call_stack[-1]
        _logger.debug(f"[label fetcher] on: {top_of_stack.name}")
        _labels: set[str] = set()
        if top_of_stack == TraverseStackElement.CARD:
            card_json = caller_json
            for k, v in card_json.items():
                if (k == "description") or (k == "name"):
                    if v is not None:
                        _labels.add(v)
        elif top_of_stack == TraverseStackElement.VISUALIZATION_SETTINGS:
            viz_set = caller_json
            for k, v in viz_set.items():
                if (
                    (k == "text")
                    or (k == "graph.x_axis.title_text")
                    or (k == "graph.y_axis.title_text")
                    or k.endswith("title_text")
                ):
                    _labels.add(v)
        elif top_of_stack == TraverseStackElement.COLUMN_SETTINGS:
            cols_set = caller_json
            for _, d in cols_set.items():
                for k, v in d.items():
                    if k == "column_title":
                        _labels.add(v)
        elif top_of_stack == TraverseStackElement.SERIES_SETTINGS:
            series_set = caller_json
            for _, d in series_set.items():
                for k, v in d.items():
                    if k == "title":
                        _labels.add(v)
        return ReturnValue(_labels)

    def _label_replacer(
        self, caller_json: dict, call_stack: TraverseStack, labels_repl: dict[str, str]
    ) -> ReturnValue:
        if call_stack.empty:
            raise RuntimeError("Call stack is empty - this shouldn't happen!")
        top_of_stack = call_stack[-1]
        _logger.debug(f"[label fetcher] on: {top_of_stack.name}")
        _labels: set[str] = set()
        if top_of_stack == TraverseStackElement.CARD:
            card_json = caller_json
            for k, v in card_json.items():
                if (k == "description") or (k == "name"):
                    if v is not None:
                        card_json[k] = labels_repl.get(v, v)
        elif top_of_stack == TraverseStackElement.VISUALIZATION_SETTINGS:
            viz_set = caller_json
            for k, v in viz_set.items():
                if (
                    (k == "text")
                    or (k == "graph.x_axis.title_text")
                    or (k == "graph.y_axis.title_text")
                    or k.endswith("title_text")
                ):
                    viz_set[k] = labels_repl.get(v, v)
        elif top_of_stack == TraverseStackElement.COLUMN_SETTINGS:
            cols_set = caller_json
            for _, d in cols_set.items():
                for k, v in d.items():
                    if k == "column_title":
                        d[k] = labels_repl.get(v, v)
        elif top_of_stack == TraverseStackElement.SERIES_SETTINGS:
            series_set = caller_json
            for _, d in series_set.items():
                for k, v in d.items():
                    if k == "title":
                        d[k] = labels_repl.get(v, v)
        return ReturnValue(None)

    def _number_formatter(
        self, caller_json: dict, call_stack: TraverseStack
    ) -> ReturnValue:
        def _formatting_settings_from(d: dict) -> dict:
            """Builds the dictionary for number formatting."""
            sep = ", "
            number_style = "decimal"
            is_currency = ("prefix" in d) and (d["prefix"] == "$")
            return {
                "number_style": number_style,
                "number_separators": sep,
                "suffix": " $" if is_currency else d.get("suffix", ""),
                "prefix": "" if is_currency else d.get("prefix", ""),
            }

        if call_stack.empty:
            raise RuntimeError("Call stack is empty - this shouldn't happen!")
        top_of_stack = call_stack[-1]
        _logger.debug(f"[number formatter] on: {top_of_stack.name}")
        if top_of_stack == TraverseStackElement.COLUMN_SETTINGS:
            column_settings = caller_json
            for _col_set_k, _a_dict in column_settings.items():
                # sanity check. Probably not needed.
                assert isinstance(_a_dict, dict)
                # let's take care of the formatting elements on one side, and the rest on another
                formatting_d = _formatting_settings_from(_a_dict)
                rest_of_d = deepcopy(
                    {k: v for (k, v) in _a_dict.items() if k not in formatting_d.keys()}
                )
                # and now I combine both
                column_settings[_col_set_k] = formatting_d | rest_of_d
        return ReturnValue(None)

    def traverse(
        self,
        f: Callable[[dict, TraverseStack], ReturnValue],
        call_stack: Optional[TraverseStack] = None,
    ) -> ReturnValue:
        def _traverse_query_part(query_part: dict) -> ReturnValue:
            with call_stack.add(TraverseStackElement.QUERY_PART):
                r = f(query_part, call_stack)
                if "source-query" in query_part:
                    r1 = _traverse_query_part(query_part["source-query"])
                    r = r.union(r1)
            return r

        def _visualization_settings(viz_settings: dict) -> ReturnValue:
            with call_stack.add(TraverseStackElement.VISUALIZATION_SETTINGS):
                r = f(viz_settings, call_stack)
                for k, v in viz_settings.items():
                    if k == "table.columns":
                        all_table_columns = v
                        for table_column in all_table_columns:
                            with call_stack.add(TraverseStackElement.TABLE_COLUMN):
                                f(table_column, call_stack)
                        with call_stack.add(TraverseStackElement.TABLE_COLUMNS):
                            r = f(all_table_columns, call_stack)
                            if r.v is not None:
                                new_table_columns = list(r.v)
                                viz_settings["table.columns"] = new_table_columns
                    elif k == "click_behavior":
                        click_behavior = v
                        with call_stack.add(TraverseStackElement.CLICK_BEHAVIOR):
                            f(click_behavior, call_stack)
                        if "parameterMapping" in click_behavior:
                            with call_stack.add(TraverseStackElement.PARAMETER_MAPPING):
                                f(click_behavior["parameterMapping"], call_stack)
                    elif k == "graph.dimensions":
                        graph_dimensions = v
                        with call_stack.add(TraverseStackElement.GRAPH_DIMENSIONS):
                            r = f(graph_dimensions, call_stack)
                            if r.v is not None:
                                _l = list(r.v)
                                viz_settings["graph.dimensions"] = _l
                    elif k == "column_settings":
                        column_settings = v
                        with call_stack.add(TraverseStackElement.COLUMN_SETTINGS):
                            r = f(column_settings, call_stack)
                            for _col_set_k, _a_dict in column_settings.items():
                                if _col_set_k == "click_behavior":
                                    with call_stack.add(
                                        TraverseStackElement.CLICK_BEHAVIOR
                                    ):
                                        f(_a_dict, call_stack)
                    elif k == "series_settings":
                        series_settings = v
                        with call_stack.add(TraverseStackElement.SERIES_SETTINGS):
                            f(series_settings, call_stack)
            return r

        # nb: I am using here self.card_json, which means that it will have to be
        # put up-to-date before making this call.
        _logger.info(f"Visiting card id '{self.card_id}'")
        if call_stack is None:
            call_stack = TraverseStack()
        with call_stack.add(TraverseStackElement.CARD):
            # let's first apply the function to the card itself
            r = f(self.card_json, call_stack)
            # ...and then let's go on each of its sub-parts
            if "dataset_query" in self.card_json:
                if "query" in self.card_json["dataset_query"]:
                    r1 = _traverse_query_part(
                        query_part=self.card_json["dataset_query"]["query"]
                    )
                    r = r.union(r1)
            if "visualization_settings" in self.card_json:
                r1 = _visualization_settings(self.card_json["visualization_settings"])
                r = r.union(r1)
        return r

    def migrate(self, params: "CardParameters", push: bool = True) -> bool:
        """Migrates a card, based on a set of parameters. Pushes if flag is True."""
        from metabase_api.migration.defs import migration_function

        if self.card_id in MIGRATED_CARDS:
            _logger.debug(f"[already visited card id '{self.card_id}']")
            return True
        self.traverse(
            f=lambda a_json, a_stack: migration_function(
                caller_json=a_json, params=params, call_stack=a_stack
            ),
        )
        success: bool
        if push:
            success = self.push(metabase_api=params.metabase_api)
        else:
            success = True
        if success:
            MIGRATED_CARDS.append(self.card_id)
        return success

    @property
    def labels(self) -> set[str]:
        if len(self._labels) == 0:
            self._labels = self.clean_labels(
                set(self.traverse(f=self._label_fetcher).v)
            )
        return self._labels

    def translate(self, translation_dict: dict[str, str]):
        self.traverse(
            f=lambda a_json, a_stack: self._label_replacer(
                caller_json=a_json, call_stack=a_stack, labels_repl=translation_dict
            ),
        )

    def push(self, metabase_api: Metabase_API) -> bool:
        return metabase_api.put(f"/api/card/{self.card_id}", json=self.card_json) == 200
