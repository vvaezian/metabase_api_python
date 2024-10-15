import logging
from copy import deepcopy
from typing import Optional

from metabase_api.objects.defs import TraverseStack, ReturnValue, TraverseStackElement
from metabase_api.utility.options import NumberFormat
from copy import copy

_logger = logging.getLogger(__name__)


def number_formatter(
    caller_json: dict,  # type:ignore
    number_format: NumberFormat,
    call_stack: TraverseStack,
) -> ReturnValue:
    def _is_column_numeric(column_d: dict[str, str]) -> bool:
        """Based on the definition of the column, tries to determine if it is numeric."""
        FIELDS_IN_NUMERIC_COLUMN = {
            "number_style",
            "number_separators",
            "suffix",
            "prefix",
            "currency_in_header",
            "decimals",
        }
        if len(FIELDS_IN_NUMERIC_COLUMN.intersection(column_d.keys())) > 0:
            return True
        return False

    def _formatting_settings_from(
        parent_title: str, d: dict[str, str]
    ) -> dict[str, str]:
        """Builds the dictionary for number formatting."""
        CURRENCY_HINTS = {"cost", "price", "money", "income"}
        parent_title_looks_like_currency = (
            next(
                (x for x in CURRENCY_HINTS if x in parent_title.lower()),
                None,
            )
            is not None
        )
        title_looks_like_currency = (
            next(
                (x for x in CURRENCY_HINTS if x in d.get("column_title", "").lower()),
                None,
            )
            is not None
        )
        is_currency = (
            (d.get("prefix", "") == "$")
            or (d.get("suffix", "") == "$")
            or (d.get("number_style", "") == "currency")
            or ("currency_in_header" in d)
            or title_looks_like_currency
            or parent_title_looks_like_currency
        )
        common = {
            "number_style": number_format.number_style,
            "number_separators": number_format.number_separators,
        }
        suffix_prefix = {
            "suffix": number_format.number_currency_suffix
            if is_currency
            else number_format.number_other_suffix,
            "prefix": number_format.number_currency_prefix
            if is_currency
            else number_format.number_other_prefix,
        }
        return common | suffix_prefix

    def _enclosing_card_title(_stack_copy: TraverseStack) -> Optional[str]:
        """Go up in stack until I find a card - and return its name. None if no card."""
        if len(_stack_copy) == 0:
            return None
        top = _stack_copy.top
        if top == TraverseStackElement.CARD:
            return top.title
        return _enclosing_card_title(_stack_copy.bottom)

    if call_stack.empty:
        raise RuntimeError("Call stack is empty - this shouldn't happen!")
    top_of_stack: TraverseStackElement = call_stack.top
    modified: bool = False
    if top_of_stack == TraverseStackElement.COLUMN_SETTINGS:
        column_settings = caller_json
        for _col_set_k, _a_dict in column_settings.items():
            # sanity check. Probably not needed.
            assert isinstance(_a_dict, dict)
            if _is_column_numeric(column_d=_a_dict):
                # let's take care of the formatting elements on one side, and the rest on another
                card_title_opt: Optional[str] = _enclosing_card_title(copy(call_stack))
                formatting_d = _formatting_settings_from(
                    parent_title="" if card_title_opt is None else card_title_opt,
                    d=_a_dict,
                )
                rest_of_d = deepcopy(
                    {k: v for (k, v) in _a_dict.items() if k not in formatting_d.keys()}
                )
                # and now I combine both
                column_settings[_col_set_k] = formatting_d | rest_of_d
                modified = True
    if modified:
        _logger.debug(
            f"[number formatter] worked on {top_of_stack.name} (stack: {call_stack})"
        )
    return ReturnValue(None)


def label_fetcher(
    caller_json: dict,  # type:ignore
    call_stack: TraverseStack,
) -> ReturnValue:
    """Fetches labels from a structure."""
    if call_stack.empty:
        raise RuntimeError("Call stack is empty - this shouldn't happen!")
    top_of_stack = call_stack.top
    _labels: set[str] = set()
    modified = False
    if top_of_stack == TraverseStackElement.CARD:
        card_json = caller_json
        for k, v in card_json.items():
            if (k == "description") or (k == "name"):
                if v is not None:
                    _labels.add(v)
                    modified = True
    elif top_of_stack == TraverseStackElement.DASHBOARD:
        dash = caller_json
        for k, v in dash.items():
            if k in {"description", "name"}:
                _labels.add(v)
                modified = True
    elif top_of_stack == TraverseStackElement.TABS:
        tabs = caller_json
        for a_tab in tabs:
            _labels.add(a_tab["name"])
            modified = True
    elif top_of_stack == TraverseStackElement.PARAMETER:
        params_dict = caller_json
        _labels.add(params_dict["name"])
        modified = True
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
                modified = True
    elif top_of_stack == TraverseStackElement.COLUMN_SETTINGS:
        cols_set = caller_json
        for _, d in cols_set.items():
            for k, v in d.items():
                if k == "column_title":
                    _labels.add(v)
                    modified = True
    elif top_of_stack == TraverseStackElement.SERIES_SETTINGS:
        series_set = caller_json
        for _, d in series_set.items():
            for k, v in d.items():
                if k == "title":
                    _labels.add(v)
                    modified = True
    if modified:
        _logger.debug(
            f"[label fetcher] grabbed label(s) from {top_of_stack.name} (stack: {call_stack})"
        )
    return ReturnValue(_labels)


def label_replacer(
    caller_json: dict,  # type:ignore
    call_stack: TraverseStack,
    labels_repl: dict[str, str],
) -> ReturnValue:
    def _try_replace_str(v: str) -> tuple[bool, str]:
        """Searches for a replacement for the input string; returns it along with a flag (True if replaced)."""
        changed: bool
        # we'll handle the string as-is first, but also we'll look at the case were the string
        # is surrounded by white-spaces
        repl = labels_repl.get(v, v)
        changed = repl != v
        if changed:
            return changed, repl
        # ok, then let's handle whitespaces
        # how many at the left? And at the right?
        lblanks = len(v) - len(v.lstrip())
        rblanks = len(v) - len(v.rstrip())
        v = v.strip()
        repl = labels_repl.get(v, v)
        # let's re-add the white spaces
        repl = " " * lblanks + repl + " " * rblanks
        return repl != v, repl

    if call_stack.empty:
        raise RuntimeError("Call stack is empty - this shouldn't happen!")
    top_of_stack = call_stack.top
    _labels: set[str] = set()
    modified: bool = False
    if top_of_stack == TraverseStackElement.CARD:
        card_json = caller_json
        for k, v in card_json.items():
            if (k == "description") or (k == "name"):
                if v is not None:
                    modified, card_json[k] = _try_replace_str(v)
    elif top_of_stack == TraverseStackElement.DASHBOARD:
        dash = caller_json
        for k, v in dash.items():
            if k in {"description", "name"}:
                modified, dash[k] = _try_replace_str(v)
    elif top_of_stack == TraverseStackElement.TABS:
        tabs = caller_json
        for a_tab in tabs:
            modified, a_tab["name"] = _try_replace_str(a_tab["name"])
    elif top_of_stack == TraverseStackElement.PARAMETER:
        params_dict = caller_json
        modified, params_dict["name"] = _try_replace_str(params_dict["name"])
    elif top_of_stack == TraverseStackElement.VISUALIZATION_SETTINGS:
        modified = True
        viz_set = caller_json
        for k, v in viz_set.items():
            if (
                (k == "text")
                or (k == "graph.x_axis.title_text")
                or (k == "graph.y_axis.title_text")
                or k.endswith("title_text")
            ):
                modified, viz_set[k] = _try_replace_str(v)
    elif top_of_stack == TraverseStackElement.COLUMN_SETTINGS:
        cols_set = caller_json
        for _, d in cols_set.items():
            for k, v in d.items():
                if k == "column_title":
                    modified, d[k] = _try_replace_str(v)
    elif top_of_stack == TraverseStackElement.SERIES_SETTINGS:
        series_set = caller_json
        for _, d in series_set.items():
            for k, v in d.items():
                if k == "title":
                    modified, d[k] = _try_replace_str(v)
    if modified:
        _logger.debug(
            f"[label replacer] modified on: {top_of_stack.name} (stack: {call_stack})"
        )
    return ReturnValue(None)
