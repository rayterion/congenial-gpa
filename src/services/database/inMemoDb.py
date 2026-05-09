from __future__ import annotations

from collections.abc import Hashable
from copy import deepcopy
from typing import Any


class InMemoryDatabase:
    """
    A simple single-table in-memory database.

    The database stores values by row and column.

    Internally, the data looks like this:

        {
            row_key: {
                column_key: value
            }
        }

    Example:
        db = InMemoryDatabase()

        db.add_cell("row1", "name", "Martin")
        db.add_cell("row1", "age", 20)

        name = db.get_cell("row1", "name")
        print(name)
    """

    def __init__(self) -> None:
        self._data: dict[Hashable, dict[Hashable, Any]] = {}

    def add_cell(self, row: Hashable, column: Hashable, value: Any) -> None:
        """
        Add or replace a cell value.

        If the row does not exist yet, it is created automatically.

        Args:
            row: The row identifier.
            column: The column identifier.
            value: The value to store.
        """
        if row not in self._data:
            self._data[row] = {}

        self._data[row][column] = value

    def get_cell(self, row: Hashable, column: Hashable, default: Any = None) -> Any:
        """
        Get a cell value by row and column.

        Args:
            row: The row identifier.
            column: The column identifier.
            default: The value returned when the cell does not exist.

        Returns:
            The stored value, or the default value if the cell does not exist.
        """
        return self._data.get(row, {}).get(column, default)

    def remove_cell(self, row: Hashable, column: Hashable) -> None:
        """
        Remove a cell from the database.

        If the row or column does not exist, nothing happens.

        Args:
            row: The row identifier.
            column: The column identifier.
        """
        if row not in self._data:
            return

        self._data[row].pop(column, None)

        if not self._data[row]:
            self._data.pop(row)

    def get_row(self, row: Hashable) -> dict[Hashable, Any]:
        """
        Get a copy of one row.

        Args:
            row: The row identifier.

        Returns:
            A dictionary with the row data.
            Returns an empty dictionary if the row does not exist.
        """
        return deepcopy(self._data.get(row, {}))

    def get_column(self, column: Hashable) -> dict[Hashable, Any]:
        """
        Get all values from one column.

        Args:
            column: The column identifier.

        Returns:
            A dictionary where each key is a row and each value is the cell value.
        """
        result: dict[Hashable, Any] = {}

        for row, columns in self._data.items():
            if column in columns:
                result[row] = deepcopy(columns[column])

        return result

    def has_cell(self, row: Hashable, column: Hashable) -> bool:
        """
        Check whether a cell exists.

        Args:
            row: The row identifier.
            column: The column identifier.

        Returns:
            True if the cell exists, otherwise False.
        """
        return row in self._data and column in self._data[row]

    def clear(self) -> None:
        """
        Clear the whole database.
        """
        self._data.clear()

    def to_dict(self) -> dict[Hashable, dict[Hashable, Any]]:
        """
        Get a full copy of the database.

        Returns:
            A copy of the internal database dictionary.
        """
        return deepcopy(self._data)