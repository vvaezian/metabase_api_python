import abc
import logging
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable, Any, Optional

from metabase_api import Metabase_API
from metabase_api.utility.db.tables import TablesEquivalencies
from metabase_api.utility.options import Options
from metabase_api.utility.translation import Language

_logger = logging.getLogger(__name__)


class TraverseStackElement(Enum):
    """All the elements I can visit when I am traversing an object."""

    CARD = auto()
    VISUALIZATION_SETTINGS = auto()
    QUERY_PART = auto()
    TABLE_COLUMN = auto()
    TABLE_COLUMNS = auto()
    CLICK_BEHAVIOR = auto()
    PARAMETER_MAPPING = auto()
    GRAPH_DIMENSIONS = auto()
    COLUMN_SETTINGS = auto()
    SERIES_SETTINGS = auto()


class TraverseStack(list[TraverseStackElement]):
    """A stack containing the elements we visit."""

    def __init__(self):
        super().__init__()

    def add(self, elt: TraverseStackElement) -> "TraverseStack":
        self.append(elt)
        return self

    @property
    def empty(self) -> bool:
        return len(self) == 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _ = self.pop()


class ReturnValue:
    """todo: document."""

    def __init__(self, v: Any):
        self.v = v

    def union(self, v: Any) -> "ReturnValue":
        if isinstance(v, ReturnValue):
            v = v.v
        # union-ing with None always works:
        if self.v is None:
            return ReturnValue(v)
        # two values need to be the same type
        if not isinstance(v, type(self.v)):
            raise TypeError("Impossible to union")
        if isinstance(self.v, set):
            return ReturnValue(set(self.v).union(set(v)))
        if isinstance(self.v, list):
            return ReturnValue(self.v + v)
        raise NotImplementedError("not sure what happened here")


class CollectionObject(abc.ABC):
    """Any object that can appear on a collection."""

    def __init__(self):
        pass

    @property
    @abc.abstractmethod
    def labels(self) -> set[str]:
        """Returns all labels found in this object."""
        pass

    @abc.abstractmethod
    def traverse(
        self,
        f: Callable[[dict, TraverseStack], ReturnValue],
        call_stack: Optional[TraverseStack] = None,
    ) -> ReturnValue:
        """
        Traverses the object, applying a function to the visited place.
        Args:
            f: function to apply
            call_stack: stack to know where these calls originated from.

        Returns:
            The same value as 'f'
        """
        pass

    def clean_labels(self, labels: set[str]) -> set[str]:
        return {l.strip() for l in labels if len(l.strip()) > 0}


@dataclass
class CardParameters:
    """Encapsulates logic for migration of a card."""

    lang: Language
    metabase_api: Metabase_API
    db_target: int
    transformations: dict
    table_equivalencies: TablesEquivalencies
    personalization_options: Options

    def replace_column_id(self, column_id: int) -> int:
        """todo: doc."""
        (
            new_field_id,
            t_src,
            t_target,
        ) = self.table_equivalencies.column_equivalent_and_details_for(
            column_id=column_id
        )
        # this column I just updated - does it appear among the ones to be replaced?
        c_to_id = self.personalization_options.replacement_column_id_for(
            column_id=new_field_id, t=t_target
        )
        if c_to_id is not None:  # None == 'no replacement specified'
            return c_to_id
        else:
            return new_field_id

    def _handle_condition_filter(self, filter_parts: Any):
        # todo: do I need to return anything....?
        def _is_cmp_op(op: str) -> bool:
            # cmp operator (like '>', '=', ...)
            return (op == ">") or (op == "=") or (op == "<=>")

        def _is_logical_op(op: str) -> bool:
            # logical operator
            return (op == "or") or (op == "and")

        if isinstance(filter_parts, list):
            op = filter_parts[0].strip()
            if op == "field":
                # reference to a table's column. Replace it.
                field_info = filter_parts
                old_field_id = field_info[1]
                if isinstance(old_field_id, int):
                    field_info[1] = self.replace_column_id(old_field_id)
            elif _is_cmp_op(op) or _is_logical_op(op) or (op.strip() == "starts-with"):
                self._handle_condition_filter(filter_parts=filter_parts[1])
                self._handle_condition_filter(filter_parts=filter_parts[2])
            else:
                raise RuntimeError(f"Luis, this should be a constant: '{op}'... is it?")

    def _replace_field_info_refs(
        self,
        field_info: list,
    ) -> list:
        if field_info[0] == "field":
            # reference to a table's column. Replace it.
            old_field_id = field_info[1]
            if isinstance(old_field_id, int):
                # if it's already migrated, then don't try to redo it.
                if (
                    self.table_equivalencies.target_table_for_column(
                        column_id=old_field_id
                    )
                    is None
                ):
                    field_info[1] = self.replace_column_id(column_id=old_field_id)
            else:
                # here: is old_field_id actually the NAME of a field we are replacing
                # (through perso_options)?
                # if so: replace
                # otherwise: leave it alone.
                _r = self.personalization_options.fields_replacements.get(
                    old_field_id, None
                )
                if _r is not None:
                    field_info[1] = _r
                else:
                    _logger.warning(
                        f"All good here????? I don't have to replace '{old_field_id}'...?"
                    )
        else:
            for idx, item in enumerate(field_info):
                if isinstance(item, list):
                    field_info[idx] = self._replace_field_info_refs(
                        item,
                    )
        return field_info
