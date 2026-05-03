import pytest
from unittest.mock import MagicMock
from apps.cli_commands import (
    execute_command,
    COMMANDS,
)


def make_api(responses: dict | None = None):
    """Build a mock ApiClient with pre-canned responses."""
    api = MagicMock()
    if responses:
        for method_name, return_value in responses.items():
            getattr(api, method_name).return_value = return_value
    return api


class TestAddCell:
    def test_add_cell_calls_api_and_returns_success(self):
        """execute_command /add_cell calls set_cell and returns a success message."""
        api = make_api({"set_cell": {"ok": True}})
        result = execute_command("/add_cell users 1 name Martin", api)
        api.set_cell.assert_called_once_with("users", "1", "name", "Martin")
        assert any(w in result.lower() for w in ["success", "ok", "done", "created"])

    def test_add_cell_missing_args_returns_error(self):
        """execute_command /add_cell with too few args returns a missing-args error."""
        api = make_api()
        result = execute_command("/add_cell users 1", api)
        assert any(w in result.lower() for w in ["missing", "required", "argument", "usage"])
        api.set_cell.assert_not_called()


class TestGetCell:
    def test_get_cell_calls_api_and_returns_value(self):
        """execute_command /get_cell calls get_cell and shows the value."""
        api = make_api({"get_cell": {"value": "Martin"}})
        result = execute_command("/get_cell users 1 name", api)
        api.get_cell.assert_called_once_with("users", "1", "name")
        assert "Martin" in result

    def test_get_cell_shows_not_found_when_missing(self):
        """execute_command /get_cell shows not-found when the API says 404."""
        api = make_api({"get_cell": None})
        result = execute_command("/get_cell users 1 name", api)
        assert any(p in result.lower() for p in ["not found", "404", "does not exist", "no such"])


class TestUpdateCell:
    def test_update_cell_calls_api_and_returns_success(self):
        """execute_command /update_cell calls update_cell and returns success."""
        api = make_api({"update_cell": {"ok": True}})
        result = execute_command("/update_cell users 1 name Tulio", api)
        api.update_cell.assert_called_once_with("users", "1", "name", "Tulio")
        assert any(w in result.lower() for w in ["success", "ok", "done", "updated"])


class TestRemoveCell:
    def test_remove_cell_calls_api_and_returns_success(self):
        """execute_command /remove_cell calls delete_cell and returns success."""
        api = make_api({"delete_cell": {"ok": True}})
        result = execute_command("/remove_cell users 1 name", api)
        api.delete_cell.assert_called_once_with("users", "1", "name")
        assert any(w in result.lower() for w in ["success", "ok", "done", "removed"])


class TestAddRow:
    def test_add_row_parses_key_value_pairs_and_calls_api(self):
        """execute_command /add_row parses key=value args and calls add_row."""
        api = make_api({"add_row": {"ok": True}})
        result = execute_command("/add_row users 1 name=Martin age=20 role=developer", api)
        api.add_row.assert_called_once_with(
            "users", "1", {"name": "Martin", "age": "20", "role": "developer"}
        )
        assert any(w in result.lower() for w in ["success", "ok", "done", "created"])


class TestGetRow:
    def test_get_row_calls_api_and_shows_all_fields(self):
        """execute_command /get_row calls get_row and displays all field values."""
        api = make_api({"get_row": {"name": "Martin", "age": "20", "role": "developer"}})
        result = execute_command("/get_row users 1", api)
        api.get_row.assert_called_once_with("users", "1")
        assert "Martin" in result
        assert "developer" in result

    def test_get_row_shows_not_found_when_missing(self):
        """execute_command /get_row shows not-found when the API returns None."""
        api = make_api({"get_row": None})
        result = execute_command("/get_row users 1", api)
        assert any(p in result.lower() for p in ["not found", "404", "does not exist", "no such"])


class TestUpdateRow:
    def test_update_row_parses_key_value_pairs_and_calls_api(self):
        """execute_command /update_row parses key=value args and calls update_row."""
        api = make_api({"update_row": {"ok": True}})
        result = execute_command("/update_row users 1 name=Tulio age=21 role=engineer", api)
        api.update_row.assert_called_once_with(
            "users", "1", {"name": "Tulio", "age": "21", "role": "engineer"}
        )
        assert any(w in result.lower() for w in ["success", "ok", "done", "updated"])


class TestRemoveRow:
    def test_remove_row_calls_api_and_returns_success(self):
        """execute_command /remove_row calls delete_row and returns success."""
        api = make_api({"delete_row": {"ok": True}})
        result = execute_command("/remove_row users 1", api)
        api.delete_row.assert_called_once_with("users", "1")
        assert any(w in result.lower() for w in ["success", "ok", "done", "removed"])


class TestListRows:
    def test_list_rows_calls_api_and_shows_all_row_values(self):
        """execute_command /list_rows calls list_rows and shows every field value."""
        api = make_api({
            "list_rows": {
                "1": {"name": "Martin", "age": "20"},
                "2": {"name": "Ana", "age": "22"},
            }
        })
        result = execute_command("/list_rows users", api)
        api.list_rows.assert_called_once_with("users")
        assert "Martin" in result
        assert "Ana" in result


class TestClearDatabase:
    def test_clear_database_calls_api_and_returns_success(self):
        """execute_command /clear_database calls clear_database and returns success."""
        api = make_api({"clear_database": {"ok": True}})
        result = execute_command("/clear_database", api)
        api.clear_database.assert_called_once()
        assert any(w in result.lower() for w in ["success", "ok", "done", "cleared"])


class TestHelp:
    def test_help_shows_commands_section(self):
        """execute_command /help returns output containing all command names."""
        api = make_api()
        result = execute_command("/help", api)
        for cmd in COMMANDS:
            assert cmd in result, f"Expected '{cmd}' in /help output"


class TestUnknownCommand:
    def test_unknown_command_returns_error(self):
        """execute_command with an unknown name returns an error message."""
        api = make_api()
        result = execute_command("/unknown_cmd", api)
        assert any(p in result.lower() for p in ["unknown", "unrecognized", "not recognized", "invalid"])
