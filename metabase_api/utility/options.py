import logging
import os
from dataclasses import dataclass
from pathlib import Path
import json
from typing import Optional

import fastjsonschema

from metabase_api.utility.db.tables import Table
from metabase_api.utility.translation import Language

_logger = logging.getLogger(__name__)


THIS_FILE_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
JSON_SCHEMA_LOC = (THIS_FILE_PATH / "personalization_json_schema.json").resolve()


@dataclass
class Options:
    """Migration options."""

    fields_replacements: dict[str, str]
    language: Language

    @classmethod
    def from_json_file(cls, p: Path) -> "Options":
        if not p.exists():
            raise FileNotFoundError(p)
        if p.suffix != ".json":
            raise ValueError(f"Personalization file must be a json (got '{str(p)}')")
        _logger.info(f"Reading personalization options from '{str(p)}'...")
        with open(p) as f:
            personalization_dict = json.load(f)
        _logger.debug(
            f"Parsing personalization options using '{str(JSON_SCHEMA_LOC)}'..."
        )
        with open(JSON_SCHEMA_LOC) as f:
            json_schema = json.load(f)
        validate = fastjsonschema.compile(json_schema)
        try:
            validate(personalization_dict)
        except fastjsonschema.exceptions.JsonSchemaValueException as json_exc:
            raise ValueError(
                f"Structure in '{str(p)}' does not look like a personalisation file"
            ) from json_exc
        return Options(
            fields_replacements=personalization_dict["fields_replacements"],
            language=Language[personalization_dict["language"]],
        )

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
