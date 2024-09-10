import logging
from dataclasses import dataclass, field
from typing import Optional

from metabase_api import Metabase_API
from metabase_api._helper_methods import ItemType
from metabase_api.utility.db.columns import ColumnReferences

_logger = logging.getLogger(__name__)


class Table:
    """What do we want to keep about tables."""

    def __init__(
        self,
        metabase_api: Metabase_API,
        db_id: int,
        table_id: int,
        column_references: ColumnReferences,
    ):
        self.metabase_api = metabase_api
        self.db_id = db_id
        self.db_name = self.metabase_api.get_item_name(
            item_type="database", item_id=self.db_id
        )
        self.unique_id = table_id
        self.name = self.metabase_api.get_item_name(
            item_type="table", item_id=self.unique_id
        )
        self.column_references = column_references
        _logger.debug(f"Registered {str(self)}")

    @classmethod
    def from_id(cls, metabase_api: Metabase_API, table_id: int) -> "Table":
        _logger.debug(f"Fetching table {table_id}")
        db_id = metabase_api.get_db_id_from_table_id(table_id=table_id)
        column_references = ColumnReferences.from_metabase(
            metabase_api=metabase_api, table_id=table_id
        )
        return Table(
            metabase_api=metabase_api,
            db_id=db_id,
            table_id=table_id,
            column_references=column_references,
        )

    @classmethod
    def from_name_and_db(
        cls, metabase_api: Metabase_API, table_name: str, db_id: int
    ) -> "Table":
        _logger.debug(f"Fetching table {table_name} in db {db_id}")
        table_id = metabase_api.get_item_id(
            item_type=ItemType.TABLE, item_name=table_name, db_id=db_id
        )
        return Table.from_id(metabase_api=metabase_api, table_id=table_id)

    def get_column_name(self, column_id: int) -> str:
        """ValueError if impossible to fetch."""
        return self.column_references.get_column_name(column_id=column_id)

    def get_column_id(self, column_name: str) -> int:
        """ValueError if impossible to fetch."""
        return self.column_references.get_column_id(column_name=column_name)

    def __str__(self) -> str:
        return f"[db: '{self.db_name}' (id:{self.db_id})] Table '{self.name}' (id:{self.unique_id})"


@dataclass
class TablesEquivalencies:
    """A bunch of equivalencies between tables.
    We explicitly enforce that the _destination_ bd is only ONE
    (ie, the equivalencies can not refer to different target databases).
    We don't explicitly put any restriction on _sources_
    """

    metabase_api: Metabase_API
    dst_bd_id: int
    _src2dst: dict[Table, Table] = field(default_factory=dict)

    def __init__(self, metabase_api: Metabase_API, dst_bd_id: int):
        self.metabase_api = metabase_api
        self.dst_bd_id = dst_bd_id
        self._src2dst = dict()

    def add(self, src2dst: dict[int, int]):
        src_dbs: set[str] = set()
        for table_src_id, table_dst_id in src2dst.items():
            if table_dst_id in self.src_tables_ids:
                raise KeyError(
                    f"{table_dst_id} is associated as a SOURCE table - but here it is being associated as the destination of {table_src_id}"
                )
            if table_src_id in self.src_tables_ids:
                ex_table_dst_id = self[table_src_id].unique_id
                if ex_table_dst_id != table_dst_id:
                    raise KeyError(
                        f"Table {table_src_id} is already associated with table {ex_table_dst_id} (trying to associate if with {table_dst_id})"
                    )
            table_src = Table.from_id(
                metabase_api=self.metabase_api, table_id=table_src_id
            )
            table_dst = Table.from_id(
                metabase_api=self.metabase_api, table_id=table_dst_id
            )
            _logger.debug(
                f"Recording that table {table_src_id} (db: {table_src.db_id}) is equivalent to {table_dst_id} (db: {table_dst.db_id})"
            )
            self._src2dst[table_src] = table_dst
            src_dbs.add(table_src.db_name)
        if len(src2dst.items()) > 0:
            _logger.debug(
                f"Just added {len(src2dst.items())} source tables, from {len(src_dbs)} database(s): {src_dbs}"
            )

    @property
    def src_tables_ids(self) -> list[int]:
        return [t.unique_id for t in self.src_tables]

    @property
    def dst_tables_ids(self) -> list[int]:
        """Returns ids of all tables referenced here."""
        # return self._dst_ids
        return [t.unique_id for t in self.dst_tables]

    @property
    def src_tables(self) -> list[Table]:
        return [t for t in self._src2dst.keys()]

    @property
    def dst_tables(self) -> list[Table]:
        """Returns all tables referenced here."""
        return [t for t in self._src2dst.values()]

    def _get_table(self, src_or_dst: str, table_id: int) -> Table:
        assert src_or_dst in {"src", "dst"}
        all_tables = self.src_tables if src_or_dst == "src" else self.dst_tables
        ts = [t for t in all_tables if t.unique_id == table_id]
        if len(ts) == 0:
            raise KeyError(f"Table '{table_id}' not found.")
        return ts[0]

    def get_src_table(self, table_id: int) -> Table:
        return self._get_table(src_or_dst="src", table_id=table_id)

    def get_dst_table(self, table_id: int) -> Table:
        return self._get_table(src_or_dst="dst", table_id=table_id)

    def _try_to_resolve(self, table_src_id: int) -> bool:
        """Tries to fetch the info about the table and its equivalent on a certain db."""
        # is table_src_id already mentioned as a DEST?
        d = {
            t_src.unique_id: t_dst
            for (t_src, t_dst) in self._src2dst.items()
            if t_dst.unique_id == table_src_id
        }
        if len(d) > 0:
            raise ValueError(
                f"Table {table_src_id} is already mentioned as a destination - so it can't be a source also."
            )
        try:
            table_src = Table.from_id(
                metabase_api=self.metabase_api, table_id=table_src_id
            )
            # get this id from 'column name' above AND target db id
            # -- special case: dst bd is the same as the source db.
            if table_src.db_id == self.dst_bd_id:
                # -- In that case the solution is pretty simple:
                table_dst = table_src
            else:
                # -- otherwise let's fetch it
                table_dst_id = Table.from_name_and_db(
                    metabase_api=self.metabase_api,
                    table_name=table_src.name,
                    db_id=self.dst_bd_id,
                ).unique_id
                # is table_dst_id already mentioned as a SRC?
                d = {
                    t_src.unique_id: t_dst
                    for (t_src, t_dst) in self._src2dst.items()
                    if t_src.unique_id == table_dst_id
                }
                if len(d) > 0:
                    raise ValueError(
                        f"Resolving src table {table_src_id}: table {table_dst_id} is already mentioned as a source - so it can't be a destination also."
                    )
                table_dst = Table.from_id(
                    metabase_api=self.metabase_api, table_id=table_dst_id
                )
            _logger.debug(
                f"Recording that table {str(table_src)} is equivalent to {str(table_dst)}"
            )
            self._src2dst[table_src] = table_dst
            return True
        except ValueError as ve:
            _logger.error(ve)
            return False

    def __getitem__(self, table_id: int) -> Table:
        """Table equivalent to the one mentioned. ValueError if table does not exist."""
        d = {
            t_src.unique_id: t_dst
            for (t_src, t_dst) in self._src2dst.items()
            if t_src.unique_id == table_id
        }
        if len(d) == 0:
            # go and fetch it
            if self._try_to_resolve(table_src_id=table_id):
                return self[table_id]  # it's going to work, now!
            raise KeyError(
                f"Table '{table_id}' does not have an equivalent destination."
            )
        return d[table_id]

    def target_table_for_column(self, column_id: int) -> Optional[Table]:
        """Tries to find a column id in target tables - on success, returns the Table where it's found."""
        if len(self._src2dst) == 0:
            raise ValueError("No tables have been defined as equivalent.")
        for _, table_dst in self._src2dst.items():
            try:
                column_name = table_dst.get_column_name(column_id=column_id)
            except ValueError:
                # no problemo - column is not on this table. Carry on...
                continue
            # found it! (if I am here I didn't get short-circuited by the 'continue' above)
            return table_dst
        # if I got here it's because I couldn't find the field anywhere!
        return None

    def column_equivalent_and_details_for(
        self, column_id: int
    ) -> tuple[int, Table, Table]:
        """
        Given a column id (supposedly from a 'src' table), finds the column id on a 'target' table.
        Also returns the src/target tables.
        """
        if len(self._src2dst) == 0:
            raise ValueError("No tables have been defined as equivalent.")
        for table_src, table_dst in self._src2dst.items():
            try:
                column_name = table_src.get_column_name(column_id=column_id)
            except ValueError:
                # no problemo - column is not on this table.
                # since we are here... is this column on the target table, by any chance...?
                try:
                    _ = table_dst.get_column_name(column_id=column_id)
                    # oops!!
                    raise ValueError(
                        f"Field '{column_id}' appears on a TARGET table! ({table_dst})"
                    )
                except ValueError:
                    # Carry on...
                    continue
            # found it! (if I am here I didn't get short-circuited by the 'continue' above
            return (
                table_dst.get_column_id(column_name=column_name),
                table_src,
                table_dst,
            )
        # if I got here it's because I couldn't find the field anywhere!
        raise ValueError(f"Field '{column_id}' does not appear in any source table.")

    def column_equivalent_for(self, column_id: int) -> int:
        """Looking for a column equivalence, but I don't know from what table it came from."""
        target_column, t_src, t_dst = self.column_equivalent_and_details_for(
            column_id=column_id
        )
        return target_column
