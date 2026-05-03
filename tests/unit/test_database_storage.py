import pytest
from src.services.database_storage import DatabaseStorage


class TestAddAndGetRow:
    def test_add_and_get_row_returns_stored_data(self):
        """Adding a row and getting it returns the same data."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin", "age": "20"})
        result = storage.get_row("users", "1")
        assert result == {"name": "Martin", "age": "20"}

    def test_get_nonexistent_row_returns_none(self):
        """Getting a row that does not exist returns None."""
        storage = DatabaseStorage()
        assert storage.get_row("users", "99") is None


class TestUpdateRow:
    def test_update_row_modifies_fields(self):
        """Updating a row changes the specified fields."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin"})
        storage.update_row("users", "1", {"name": "Tulio"})
        assert storage.get_row("users", "1")["name"] == "Tulio"

    def test_update_row_returns_false_when_row_does_not_exist(self):
        """Updating a nonexistent row returns False."""
        storage = DatabaseStorage()
        assert storage.update_row("users", "99", {"name": "X"}) is False


class TestDeleteRow:
    def test_delete_row_removes_it(self):
        """Deleting a row removes it from storage."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin"})
        storage.delete_row("users", "1")
        assert storage.get_row("users", "1") is None

    def test_delete_row_returns_false_when_row_does_not_exist(self):
        """Deleting a nonexistent row returns False."""
        storage = DatabaseStorage()
        assert storage.delete_row("users", "99") is False


class TestCellOperations:
    def test_get_cell_returns_value(self):
        """Getting a cell returns the stored value."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin"})
        assert storage.get_cell("users", "1", "name") == "Martin"

    def test_get_nonexistent_cell_returns_none(self):
        """Getting a cell that does not exist returns None."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin"})
        assert storage.get_cell("users", "1", "age") is None

    def test_set_cell_updates_value_in_existing_row(self):
        """Setting a cell updates the value in an existing row."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin"})
        storage.set_cell("users", "1", "age", "20")
        assert storage.get_cell("users", "1", "age") == "20"

    def test_set_cell_creates_row_when_it_does_not_exist(self):
        """Setting a cell on a nonexistent row creates the row."""
        storage = DatabaseStorage()
        storage.set_cell("users", "1", "name", "Martin")
        assert storage.get_cell("users", "1", "name") == "Martin"

    def test_delete_cell_removes_it(self):
        """Deleting a cell removes it from the row."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin"})
        storage.delete_cell("users", "1", "name")
        assert storage.get_cell("users", "1", "name") is None

    def test_delete_nonexistent_cell_returns_false(self):
        """Deleting a cell that does not exist returns False."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin"})
        assert storage.delete_cell("users", "1", "age") is False


class TestListRowsAndClear:
    def test_list_rows_returns_all_rows_in_table(self):
        """Listing rows returns all rows in the table."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin"})
        storage.add_row("users", "2", {"name": "Ana"})
        result = storage.list_rows("users")
        assert "1" in result and "2" in result

    def test_list_rows_returns_empty_for_unknown_table(self):
        """Listing rows for an unknown table returns an empty dict."""
        storage = DatabaseStorage()
        assert storage.list_rows("nonexistent") == {}

    def test_clear_removes_all_data(self):
        """Clearing storage removes all tables and rows."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin"})
        storage.clear()
        assert storage.get_row("users", "1") is None
        assert storage.list_tables() == {}

    def test_list_tables_returns_known_tables(self):
        """Listing tables returns all tables that have been written to."""
        storage = DatabaseStorage()
        storage.add_row("users", "1", {"name": "Martin"})
        storage.add_row("products", "1", {"title": "Widget"})
        tables = storage.list_tables()
        assert "users" in tables
        assert "products" in tables
