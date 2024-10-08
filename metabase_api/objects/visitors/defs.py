import logging
from copy import deepcopy

from metabase_api.objects.defs import TraverseStack, ReturnValue, TraverseStackElement
from metabase_api.utility.options import NumberFormat

_logger = logging.getLogger(__name__)


def number_formatter(
    caller_json: dict,  # type:ignore
    number_format: NumberFormat,
    call_stack: TraverseStack,
) -> ReturnValue:
    def _formatting_settings_from(d: dict[str, str]) -> dict[str, str]:
        """Builds the dictionary for number formatting."""
        CURRENCY_HINTS = {"cost", "price", "money", "income"}
        title_looks_like_currency = (
            next(
                (x for x in CURRENCY_HINTS if x in d.get("column_title", "").lower()),
                None,
            )
            is not None
        )
        is_currency = (
            (d.get("prefix", "") == "$")
            or (d.get("number_style", "") == "currency")
            or title_looks_like_currency
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


def label_fetcher(
    caller_json: dict,  # type:ignore
    call_stack: TraverseStack,
) -> ReturnValue:
    """Fetches labels from a structure."""
    if call_stack.empty:
        raise RuntimeError("Call stack is empty - this shouldn't happen!")
    top_of_stack = call_stack[-1]
    _logger.debug(f"[label fetcher] on: {top_of_stack.name}")
    _labels: set[str] = set()
    modified = False
    if top_of_stack == TraverseStackElement.CARD:
        modified = True
        card_json = caller_json
        for k, v in card_json.items():
            if (k == "description") or (k == "name"):
                if v is not None:
                    _labels.add(v)
    elif top_of_stack == TraverseStackElement.DASHBOARD:
        modified = True
        dash = caller_json
        for k, v in dash.items():
            if k in {"description", "name"}:
                _labels.add(v)
    elif top_of_stack == TraverseStackElement.TABS:
        modified = True
        tabs = caller_json
        for a_tab in tabs:
            _labels.add(a_tab["name"])
    elif top_of_stack == TraverseStackElement.PARAMETER:
        modified = True
        params_dict = caller_json
        _labels.add(params_dict["name"])
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
                _labels.add(v)
    elif top_of_stack == TraverseStackElement.COLUMN_SETTINGS:
        modified = True
        cols_set = caller_json
        for _, d in cols_set.items():
            for k, v in d.items():
                if k == "column_title":
                    _labels.add(v)
    elif top_of_stack == TraverseStackElement.SERIES_SETTINGS:
        modified = True
        series_set = caller_json
        for _, d in series_set.items():
            for k, v in d.items():
                if k == "title":
                    _labels.add(v)
    if modified:
        _logger.debug(f"[label fetcher] stack: {call_stack}")
        _logger.debug(f"[label fetcher] modified on: {top_of_stack.name}")
    return ReturnValue(_labels)


def label_replacer(
    caller_json: dict,  # type:ignore
    call_stack: TraverseStack,
    labels_repl: dict[str, str],
) -> ReturnValue:
    if call_stack.empty:
        raise RuntimeError("Call stack is empty - this shouldn't happen!")
    top_of_stack = call_stack[-1]
    _labels: set[str] = set()
    modified: bool = False
    if top_of_stack == TraverseStackElement.CARD:
        modified = True
        card_json = caller_json
        for k, v in card_json.items():
            if (k == "description") or (k == "name"):
                if v is not None:
                    card_json[k] = labels_repl.get(v, v)
    elif top_of_stack == TraverseStackElement.DASHBOARD:
        modified = True
        dash = caller_json
        for k, v in dash.items():
            if k in {"description", "name"}:
                dash[k] = labels_repl.get(v, v)
    elif top_of_stack == TraverseStackElement.TABS:
        modified = True
        tabs = caller_json
        for a_tab in tabs:
            a_tab["name"] = labels_repl.get(a_tab["name"], a_tab["name"])
    elif top_of_stack == TraverseStackElement.PARAMETER:
        modified = True
        params_dict = caller_json
        params_dict["name"] = labels_repl.get(params_dict["name"], params_dict["name"])
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
                viz_set[k] = labels_repl.get(v, v)
    elif top_of_stack == TraverseStackElement.COLUMN_SETTINGS:
        modified = True
        cols_set = caller_json
        for _, d in cols_set.items():
            for k, v in d.items():
                if k == "column_title":
                    d[k] = labels_repl.get(v, v)
    elif top_of_stack == TraverseStackElement.SERIES_SETTINGS:
        modified = True
        series_set = caller_json
        for _, d in series_set.items():
            for k, v in d.items():
                if k == "title":
                    d[k] = labels_repl.get(v, v)
    if modified:
        _logger.debug(f"[label replacer] stack: {call_stack}")
        _logger.debug(f"[label replacer] modified on: {top_of_stack.name}")
    return ReturnValue(None)
