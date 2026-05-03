"""CLI command parsing and execution."""
from dataclasses import dataclass, field
from typing import Callable

from apps.api_client import ApiClient


COMMANDS = [
    "/add_cell",
    "/get_cell",
    "/update_cell",
    "/remove_cell",
    "/add_row",
    "/get_row",
    "/update_row",
    "/remove_row",
    "/list_rows",
    "/clear_database",
    "/help",
    "/exit",
]


@dataclass
class ParsedCommand:
    name: str
    args: list[str] = field(default_factory=list)


def parse_command(text: str) -> ParsedCommand:
    parts = text.strip().split()
    return ParsedCommand(name=parts[0], args=parts[1:])


def execute_command(command_text: str, api: ApiClient) -> str:
    parsed = parse_command(command_text)
    handler = _find_handler(parsed.name)
    if handler is None:
        return _unknown_command_error(parsed.name)
    return handler(parsed.args, api)


# ──────────────────────────────────────────────────────────────────────────────
# Command handlers
# ──────────────────────────────────────────────────────────────────────────────

def _handle_add_cell(args: list[str], api: ApiClient) -> str:
    if len(args) < 4:
        return _missing_args_error("/add_cell <table> <row_id> <cell> <value>")
    table, row_id, cell, value = args[0], args[1], args[2], args[3]
    api.set_cell(table, row_id, cell, value)
    return "OK: cell created."


def _handle_get_cell(args: list[str], api: ApiClient) -> str:
    if len(args) < 3:
        return _missing_args_error("/get_cell <table> <row_id> <cell>")
    table, row_id, cell = args[0], args[1], args[2]
    result = api.get_cell(table, row_id, cell)
    if result is None:
        return "Error: not found."
    return str(result.get("value", ""))


def _handle_update_cell(args: list[str], api: ApiClient) -> str:
    if len(args) < 4:
        return _missing_args_error("/update_cell <table> <row_id> <cell> <value>")
    table, row_id, cell, value = args[0], args[1], args[2], args[3]
    api.update_cell(table, row_id, cell, value)
    return "OK: cell updated."


def _handle_remove_cell(args: list[str], api: ApiClient) -> str:
    if len(args) < 3:
        return _missing_args_error("/remove_cell <table> <row_id> <cell>")
    table, row_id, cell = args[0], args[1], args[2]
    api.delete_cell(table, row_id, cell)
    return "OK: cell removed."


def _handle_add_row(args: list[str], api: ApiClient) -> str:
    if len(args) < 2:
        return _missing_args_error("/add_row <table> <row_id> [key=value ...]")
    table, row_id = args[0], args[1]
    data = _parse_key_value_pairs(args[2:])
    api.add_row(table, row_id, data)
    return "OK: row created."


def _handle_get_row(args: list[str], api: ApiClient) -> str:
    if len(args) < 2:
        return _missing_args_error("/get_row <table> <row_id>")
    table, row_id = args[0], args[1]
    row = api.get_row(table, row_id)
    if row is None:
        return "Error: not found."
    return _format_row(row)


def _handle_update_row(args: list[str], api: ApiClient) -> str:
    if len(args) < 2:
        return _missing_args_error("/update_row <table> <row_id> [key=value ...]")
    table, row_id = args[0], args[1]
    data = _parse_key_value_pairs(args[2:])
    api.update_row(table, row_id, data)
    return "OK: row updated."


def _handle_remove_row(args: list[str], api: ApiClient) -> str:
    if len(args) < 2:
        return _missing_args_error("/remove_row <table> <row_id>")
    table, row_id = args[0], args[1]
    api.delete_row(table, row_id)
    return "OK: row removed."


def _handle_list_rows(args: list[str], api: ApiClient) -> str:
    if len(args) < 1:
        return _missing_args_error("/list_rows <table>")
    table = args[0]
    rows = api.list_rows(table)
    if not rows:
        return "No rows found."
    return _format_rows(rows)


def _handle_clear_database(args: list[str], api: ApiClient) -> str:
    api.clear_database()
    return "OK: database cleared."


def _handle_help(args: list[str], api: ApiClient) -> str:
    return _build_help_text()


# ──────────────────────────────────────────────────────────────────────────────
# Formatting helpers
# ──────────────────────────────────────────────────────────────────────────────

def _format_row(row: dict) -> str:
    return "\n".join(f"  {k}: {v}" for k, v in row.items())


def _format_rows(rows: dict) -> str:
    parts = []
    for row_id, data in rows.items():
        parts.append(f"Row {row_id}:")
        parts.append(_format_row(data))
    return "\n".join(parts)


def _build_help_text() -> str:
    lines = ["Commands:"]
    lines += [f"  {cmd}" for cmd in COMMANDS]
    return "\n".join(lines)


def _missing_args_error(usage: str) -> str:
    return f"Error: missing required argument(s).\nUsage: {usage}"


def _unknown_command_error(name: str) -> str:
    return f"Error: unknown command '{name}'. Type /help for a list of commands."


def _parse_key_value_pairs(tokens: list[str]) -> dict:
    pairs = {}
    for token in tokens:
        if "=" in token:
            key, _, value = token.partition("=")
            pairs[key] = value
    return pairs


# ──────────────────────────────────────────────────────────────────────────────
# Handler registry
# ──────────────────────────────────────────────────────────────────────────────

_HANDLERS: dict[str, Callable] = {
    "/add_cell": _handle_add_cell,
    "/get_cell": _handle_get_cell,
    "/update_cell": _handle_update_cell,
    "/remove_cell": _handle_remove_cell,
    "/add_row": _handle_add_row,
    "/get_row": _handle_get_row,
    "/update_row": _handle_update_row,
    "/remove_row": _handle_remove_row,
    "/list_rows": _handle_list_rows,
    "/clear_database": _handle_clear_database,
    "/help": _handle_help,
}


def _find_handler(command_name: str) -> Callable | None:
    return _HANDLERS.get(command_name)
