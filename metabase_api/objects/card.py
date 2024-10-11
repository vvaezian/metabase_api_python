import logging
from dataclasses import dataclass
from typing import Callable, Optional, Any

from metabase_api.metabase_api import Metabase_API
from metabase_api.objects.defs import (
    CollectionObject,
    ReturnValue,
    TraverseStackElement,
    TraverseStack,
    MigrationParameters,
)
from metabase_api.objects.visitors.defs import (
    number_formatter,
    label_replacer,
)

MIGRATED_CARDS: list[int] = list()


_logger = logging.getLogger(__name__)


@dataclass(init=False)
class Card(CollectionObject):
    """A Card! :-)"""

    def __init__(self, card_json: dict[str, Any]) -> None:
        if "model" in card_json:  # field not always there. Depends on provenance.
            assert (
                card_json["model"] == "card"
            ), f"json structure does not contain a card; it contains '{card_json['model']}'"
        super().__init__(as_json=card_json)

    @classmethod
    def from_id(cls, card_id: int, metabase_api: Metabase_API) -> "Card":
        card_json = metabase_api.get(f"/api/card/{card_id}")
        return Card(card_json=card_json)

    @property
    def card_id(self) -> int:  # todo: deprecate and use 'object_id' directly.
        return self.object_id

    def traverse(
        self,
        f: Callable[[dict[Any, Any], TraverseStack], ReturnValue],
        call_stack: Optional[TraverseStack] = None,
    ) -> ReturnValue:
        def _traverse_query_part(query_part: dict[Any, Any]) -> ReturnValue:
            assert call_stack is not None
            with call_stack.add(TraverseStackElement.QUERY_PART):
                r = f(query_part, call_stack)
                if "source-query" in query_part:
                    r1 = _traverse_query_part(query_part["source-query"])
                    r = r.union(r1)
            return r

        def _visualization_settings(viz_settings: dict[Any, Any]) -> ReturnValue:
            assert call_stack is not None
            r = ReturnValue.empty()
            with call_stack.add(TraverseStackElement.VISUALIZATION_SETTINGS):
                r = r.union(f(viz_settings, call_stack))
                for k, v in viz_settings.items():
                    if k == "table.columns":
                        all_table_columns = v
                        for table_column in all_table_columns:
                            with call_stack.add(TraverseStackElement.TABLE_COLUMN):
                                r = r.union(f(table_column, call_stack))
                    elif k == "click_behavior":
                        click_behavior = v
                        with call_stack.add(TraverseStackElement.CLICK_BEHAVIOR):
                            r = r.union(f(click_behavior, call_stack))
                        if "parameterMapping" in click_behavior:
                            with call_stack.add(TraverseStackElement.PARAMETER_MAPPING):
                                r = r.union(
                                    f(click_behavior["parameterMapping"], call_stack)
                                )
                    elif k == "column_settings":
                        column_settings = v
                        with call_stack.add(TraverseStackElement.COLUMN_SETTINGS):
                            r = r.union(f(column_settings, call_stack))
                            for _col_set_k, _a_dict in column_settings.items():
                                if _col_set_k == "click_behavior":
                                    with call_stack.add(
                                        TraverseStackElement.CLICK_BEHAVIOR
                                    ):
                                        r = r.union(f(_a_dict, call_stack))
                    elif k == "series_settings":
                        series_settings = v
                        with call_stack.add(TraverseStackElement.SERIES_SETTINGS):
                            r = r.union(f(series_settings, call_stack))
            return r

        # nb: I am using here self.as_json, which means that it will have to be
        # put up-to-date before making this call.
        _logger.info(f"Visiting card id '{self.card_id}'")
        if call_stack is None:
            call_stack = TraverseStack()
        with call_stack.add(TraverseStackElement.CARD):
            # let's first apply the function to the card itself
            r = f(self.as_json, call_stack)
            # ...and then let's go on each of its sub-parts
            if "dataset_query" in self.as_json:
                if "query" in self.as_json["dataset_query"]:
                    r1 = _traverse_query_part(
                        query_part=self.as_json["dataset_query"]["query"]
                    )
                    r = r.union(r1)
            if "visualization_settings" in self.as_json:
                r1 = _visualization_settings(self.as_json["visualization_settings"])
                r = r.union(r1)
        return r

    def migrate(self, params: MigrationParameters, push: bool) -> bool:
        """Migrates a card, based on a set of parameters. Pushes if flag is True."""
        from metabase_api.migration.defs import migration_function

        if self.card_id in MIGRATED_CARDS:
            _logger.debug(f"[already visited card id '{self.card_id}']")
            return True
        # I migrate it
        self.traverse(
            f=lambda a_json, a_stack: migration_function(
                caller_json=a_json, params=params, call_stack=a_stack
            ),
        )
        # and also I change the formatting of the numbers
        self.traverse(
            f=lambda a_json, a_stack: number_formatter(
                caller_json=a_json,
                number_format=params.personalization_options.number_format,
                call_stack=a_stack,
            ),
        )
        success = self.push(metabase_api=params.metabase_api) if push else True
        if success:
            MIGRATED_CARDS.append(self.card_id)
        return success

    def translate(self, translation_dict: dict[str, str]) -> None:
        self.traverse(
            f=lambda a_json, a_stack: label_replacer(
                caller_json=a_json, call_stack=a_stack, labels_repl=translation_dict
            ),
        )

    def push(self, metabase_api: Metabase_API) -> bool:
        return bool(
            metabase_api.put(f"/api/card/{self.card_id}", json=self.as_json) == 200
        )

    def __str__(self) -> str:
        return "Card " + str(self.as_json.get("name", "no-name-in-json"))
