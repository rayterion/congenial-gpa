"""In-memory storage for tables, rows, and cells."""
from typing import Optional


class DatabaseStorage:
    def __init__(self) -> None:
        self._tables: dict[str, dict[str, dict[str, str]]] = {}

    def add_row(self, table: str, row_id: str, data: dict) -> None:
        self._ensure_row(table, row_id).update(data)

    def get_row(self, table: str, row_id: str) -> Optional[dict]:
        return self._tables.get(table, {}).get(row_id)

    def update_row(self, table: str, row_id: str, data: dict) -> bool:
        row = self.get_row(table, row_id)
        if row is None:
            return False
        row.update(data)
        return True

    def delete_row(self, table: str, row_id: str) -> bool:
        rows = self._tables.get(table, {})
        if row_id not in rows:
            return False
        del rows[row_id]
        return True

    def get_cell(self, table: str, row_id: str, cell: str) -> Optional[str]:
        row = self.get_row(table, row_id)
        if row is None:
            return None
        return row.get(cell)

    def set_cell(self, table: str, row_id: str, cell: str, value: str) -> None:
        self._ensure_row(table, row_id)[cell] = value

    def delete_cell(self, table: str, row_id: str, cell: str) -> bool:
        row = self.get_row(table, row_id)
        if row is None or cell not in row:
            return False
        del row[cell]
        return True

    def list_rows(self, table: str) -> dict:
        return dict(self._tables.get(table, {}))

    def list_tables(self) -> dict:
        return dict(self._tables)

    def clear(self) -> None:
        self._tables = {}

    def _ensure_row(self, table: str, row_id: str) -> dict:
        self._tables.setdefault(table, {})[row_id] = self._tables.get(table, {}).get(row_id) or {}
        return self._tables[table][row_id]
