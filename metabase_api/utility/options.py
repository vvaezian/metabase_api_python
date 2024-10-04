import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import fastjsonschema

from metabase_api.utility.db.tables import Table

_logger = logging.getLogger(__name__)


THIS_FILE_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
JSON_SCHEMA_LOC = (THIS_FILE_PATH / "number_options_json_schema.json").resolve()


@dataclass
class NumberFormat:
    number_style: str
    number_separators: str
    number_currency_prefix: str
    number_currency_suffix: str
    number_other_prefix: str
    number_other_suffix: str


@dataclass
class Options:
    """Migration options."""

    fields_replacements: dict[str, str]
    labels_replacements: dict[str, str]
    number_format: NumberFormat

    @classmethod
    def from_json_files(
        cls,
        p_otheroptions_opt: Path,
        p_fields_opt: Optional[Path] = None,
        p_labels_opt: Optional[Path] = None,
    ) -> "Options":
        def _read_json(p: Path) -> dict:  # type:ignore
            if not p.exists():
                raise FileNotFoundError(p)
            if p.suffix != ".json":
                raise ValueError(f"File must be a json (got '{str(p)}')")
            _logger.info(f"Reading from '{str(p)}'...")
            with open(p) as f:
                return json.load(f)  # type:ignore

        number_options = _read_json(p_otheroptions_opt)
        _logger.debug(f"Parsing number options using '{str(JSON_SCHEMA_LOC)}'...")
        with open(JSON_SCHEMA_LOC) as f:
            json_schema = json.load(f)
        validate = fastjsonschema.compile(json_schema)
        try:
            validate(number_options)
        except fastjsonschema.exceptions.JsonSchemaValueException as json_exc:
            raise ValueError(
                f"Structure in '{str(p_otheroptions_opt)}' does not look like a number's personalisation file"
            ) from json_exc

        return Options(
            fields_replacements=_read_json(p_fields_opt)
            if p_fields_opt is not None
            else {},
            labels_replacements=_read_json(p_labels_opt)
            if p_labels_opt is not None
            else {},
            number_format=NumberFormat(
                number_style=number_options["numbers"]["number_style"],
                number_separators=number_options["numbers"]["number_separators"],
                number_currency_prefix=number_options["numbers"]["currency"]["prefix"],
                number_currency_suffix=number_options["numbers"]["currency"]["suffix"],
                number_other_prefix=number_options["numbers"]["other"]["prefix"],
                number_other_suffix=number_options["numbers"]["other"]["suffix"],
            ),
        )

    def maybe_replace_label(self, a_label: str) -> str:
        """Either it replaces the label or it returns the same."""
        return self.labels_replacements.get(a_label, a_label)

    def replacement_column_id_for(self, column_id: int, t: Table) -> Optional[int]:
        """Finds id of column replacement, if mentioned on these options."""
        # is the column on the table, actually? - next line will raise if the answer is NO
        src_column_name = t.get_column_name(column_id)
        if src_column_name not in self.fields_replacements:
            # 'column_id' is not mentioned in the perso options
            return None
        target_column_name = self.fields_replacements[src_column_name]
        # great. And what is the id of this column, please?
        try:
            return t.get_column_id(column_name=target_column_name)
        except ValueError as ve:
            # oops! There is a pair (c_from: c_to) where the source is in the table
            # but NOT the target. Let's report it.
            msg = f"Column replacement '{src_column_name}'->'{target_column_name}' identified as "
            msg += f"referring to table {str(t)};"
            msg += f" however '{target_column_name}' does not appear there."
            raise ValueError(msg) from ve
            # ok, all good. Let's now replace it
        #
        # for (
        #         c_from,
        #         c_to,
        # ) in self.fields_replacements.items():
        #     try:
        #         c_from_id = t.get_column_id(column_name=c_from)
        #     except ValueError as ve:
        #         # the specific column is not in this table - all good
        #         continue
        #     # ah, this column is in the table of the column I just replaced!
        #     # is it, indeed, the column I just changed...?
        #     if c_from_id == column_id:
        #         # yes! Who do I replace it with?
        #         try:
        #             c_to_id = t.get_column_id(column_name=c_to)
        #         except ValueError as ve:
        #             # oops! There is a pair (c_from: c_to) where the source is in the table
        #             # but NOT the target. Let's report it.
        #             msg = f"Column replacement '{c_from}'->'{c_to}' identified as "
        #             msg += f"referring to table {str(t)};"
        #             msg += f" however '{c_to}' does not appear there."
        #             raise ValueError(msg) from ve
        #         # ok, all good. Let's now replace it
        #         _logger.debug(
        #             f"Replacement on {str(t)}, {c_from}->{c_to}, successful"
        #         )
        #         return c_to_id
        # # if I am here it's because 'column_id' is not mentioned in the perso options
        # return None
