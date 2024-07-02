from metabase_api import Metabase_API


class ColumnReferences:
    """Keeps mapping between column id and name for a specified table."""

    def __init__(self, table_id: int, mapping: dict[str, int]):
        """mapping keeps id:name."""
        self.table_id = table_id
        self.mapping = mapping
        self.inv_mapping: dict[int, str] = {
            column_name: column_id for (column_id, column_name) in self.mapping.items()
        }

    @classmethod
    def from_metabase(
        cls, metabase_api: Metabase_API, table_id: int
    ) -> "ColumnReferences":
        dst_table_fields = metabase_api.get_columns_name_id(table_id=table_id)
        return ColumnReferences(table_id=table_id, mapping=dst_table_fields)

    def get_column_name(self, column_id: int) -> str:
        try:
            return self.inv_mapping[column_id]
        except KeyError as ke:
            raise ValueError(
                f"column with id {column_id} does not exist in table {self.table_id}"
            ) from ke

    def get_column_id(self, column_name: str) -> int:
        try:
            return self.mapping[column_name]
        except KeyError as ke:
            raise ValueError(
                f"column with name '{column_name}' does not exist in table {self.table_id}"
            ) from ke
