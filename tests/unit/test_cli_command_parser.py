import pytest
from apps.cli_commands import parse_command


class TestParseCommand:
    def test_parse_add_cell(self):
        """parse_command splits /add_cell into name and positional args."""
        result = parse_command("/add_cell users 1 name Martin")
        assert result.name == "/add_cell"
        assert result.args == ["users", "1", "name", "Martin"]

    def test_parse_get_cell(self):
        """parse_command splits /get_cell into name and positional args."""
        result = parse_command("/get_cell users 1 name")
        assert result.name == "/get_cell"
        assert result.args == ["users", "1", "name"]

    def test_parse_add_row_with_key_value_pairs(self):
        """parse_command preserves key=value tokens as individual args."""
        result = parse_command("/add_row users 1 name=Martin age=20")
        assert result.name == "/add_row"
        assert result.args == ["users", "1", "name=Martin", "age=20"]

    def test_parse_exit(self):
        """parse_command handles commands with no arguments."""
        result = parse_command("/exit")
        assert result.name == "/exit"
        assert result.args == []

    def test_parse_unknown_command_preserves_name(self):
        """parse_command keeps the raw command name even if unknown."""
        result = parse_command("/unknown_cmd")
        assert result.name == "/unknown_cmd"

    def test_parse_missing_args_returns_partial_args(self):
        """parse_command returns only the args that are present."""
        result = parse_command("/add_cell users 1")
        assert result.name == "/add_cell"
        assert result.args == ["users", "1"]
