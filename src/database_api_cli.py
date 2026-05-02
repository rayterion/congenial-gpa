import os
import shlex
import sys
from dataclasses import dataclass
from typing import TextIO

from database_api import (
    DatabaseApiClient,
    DatabaseApiError,
    DatabaseValueNotFoundError,
)


DEFAULT_API_BASE_URL = "http://127.0.0.1:5000"

COMMAND_USAGES = {
    "/add_cell": "/add_cell <table> <row> <cell> <value>",
    "/get_cell": "/get_cell <table> <row> <cell>",
    "/update_cell": "/update_cell <table> <row> <cell> <value>",
    "/remove_cell": "/remove_cell <table> <row> <cell>",
    "/add_row": "/add_row <table> <row> <field=value> [field=value ...]",
    "/get_row": "/get_row <table> <row>",
    "/update_row": "/update_row <table> <row> <field=value> [field=value ...]",
    "/remove_row": "/remove_row <table> <row>",
    "/list_rows": "/list_rows <table>",
    "/clear_database": "/clear_database",
    "/help": "/help",
    "/exit": "/exit",
}

AVAILABLE_COMMANDS = list(COMMAND_USAGES)


@dataclass(frozen=True)
class CommandOutcome:
    should_exit: bool = False


class CliUsageError(Exception):
    def __init__(self, usage: str):
        super().__init__(usage)
        self.usage = usage


def main(
    argv: list[str] | None = None,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
    api_base_url: str | None = None,
) -> int:
    del argv
    input_stream = input_stream or sys.stdin
    output_stream = output_stream or sys.stdout
    client = DatabaseApiClient(resolve_api_base_url(api_base_url))

    print_welcome_page(output_stream)

    return run_command_loop(client, input_stream, output_stream)


def resolve_api_base_url(api_base_url: str | None) -> str:
    return api_base_url or os.environ.get("DATABASE_API_BASE_URL", DEFAULT_API_BASE_URL)


def print_welcome_page(output_stream: TextIO) -> None:
    write_line(output_stream, "Welcome to the Database API CLI")
    print_commands_section(output_stream)


def print_commands_section(output_stream: TextIO) -> None:
    write_line(output_stream, "Commands:")
    for command, usage in COMMAND_USAGES.items():
        write_line(output_stream, f"  {command} - {usage}")


def run_command_loop(
    client: DatabaseApiClient,
    input_stream: TextIO,
    output_stream: TextIO,
) -> int:
    for command_line in input_stream:
        outcome = execute_command(command_line.strip(), client, output_stream)
        if outcome.should_exit:
            return 0

    return 0


def execute_command(
    command_line: str,
    client: DatabaseApiClient,
    output_stream: TextIO,
) -> CommandOutcome:
    command_parts = split_command_line(command_line)
    if not command_parts:
        return CommandOutcome()

    command_name = command_parts[0]
    handler = COMMAND_HANDLERS.get(command_name)
    if handler is None:
        write_line(output_stream, f"Unknown command: {command_name}")
        return CommandOutcome()

    return run_command_handler(handler, command_parts[1:], client, output_stream)


def split_command_line(command_line: str) -> list[str]:
    try:
        return shlex.split(command_line)
    except ValueError:
        return command_line.split()


def run_command_handler(
    handler,
    args: list[str],
    client: DatabaseApiClient,
    output_stream: TextIO,
) -> CommandOutcome:
    try:
        return handler(args, client, output_stream)
    except CliUsageError as error:
        write_line(output_stream, f"Missing arguments. Usage: {error.usage}")
    except DatabaseValueNotFoundError:
        write_line(output_stream, "Not found")
    except DatabaseApiError as error:
        write_line(output_stream, f"Error: {error}")

    return CommandOutcome()


def add_cell(args: list[str], client: DatabaseApiClient, output_stream: TextIO):
    table, row, cell, value = cell_write_arguments(args, COMMAND_USAGES["/add_cell"])
    client.create_cell(table, row, cell, value)
    write_line(output_stream, "Success: cell created.")

    return CommandOutcome()


def get_cell(args: list[str], client: DatabaseApiClient, output_stream: TextIO):
    table, row, cell = cell_location_arguments(args, COMMAND_USAGES["/get_cell"])
    value = client.read_cell(table, row, cell)
    write_line(output_stream, value)

    return CommandOutcome()


def update_cell(args: list[str], client: DatabaseApiClient, output_stream: TextIO):
    table, row, cell, value = cell_write_arguments(args, COMMAND_USAGES["/update_cell"])
    client.update_cell(table, row, cell, value)
    write_line(output_stream, "Success: cell updated.")

    return CommandOutcome()


def remove_cell(args: list[str], client: DatabaseApiClient, output_stream: TextIO):
    table, row, cell = cell_location_arguments(args, COMMAND_USAGES["/remove_cell"])
    client.delete_cell(table, row, cell)
    write_line(output_stream, "Success: cell removed.")

    return CommandOutcome()


def add_row(args: list[str], client: DatabaseApiClient, output_stream: TextIO):
    table, row, values = row_write_arguments(args, COMMAND_USAGES["/add_row"])
    client.create_row(table, row, values)
    write_line(output_stream, "Success: row created.")

    return CommandOutcome()


def get_row(args: list[str], client: DatabaseApiClient, output_stream: TextIO):
    table, row = row_location_arguments(args, COMMAND_USAGES["/get_row"])
    write_row(output_stream, client.read_row(table, row))

    return CommandOutcome()


def update_row(args: list[str], client: DatabaseApiClient, output_stream: TextIO):
    table, row, values = row_write_arguments(args, COMMAND_USAGES["/update_row"])
    client.update_row(table, row, values)
    write_line(output_stream, "Success: row updated.")

    return CommandOutcome()


def remove_row(args: list[str], client: DatabaseApiClient, output_stream: TextIO):
    table, row = row_location_arguments(args, COMMAND_USAGES["/remove_row"])
    client.delete_row(table, row)
    write_line(output_stream, "Success: row removed.")

    return CommandOutcome()


def list_rows(args: list[str], client: DatabaseApiClient, output_stream: TextIO):
    table = one_argument(args, COMMAND_USAGES["/list_rows"])
    rows = client.list_rows(table)
    write_rows(output_stream, rows)

    return CommandOutcome()


def clear_database(args: list[str], client: DatabaseApiClient, output_stream: TextIO):
    no_arguments(args, COMMAND_USAGES["/clear_database"])
    client.clear_database()
    write_line(output_stream, "Success: database cleared.")

    return CommandOutcome()


def show_help(args: list[str], _client: DatabaseApiClient, output_stream: TextIO):
    no_arguments(args, COMMAND_USAGES["/help"])
    print_commands_section(output_stream)

    return CommandOutcome()


def exit_cli(args: list[str], _client: DatabaseApiClient, output_stream: TextIO):
    no_arguments(args, COMMAND_USAGES["/exit"])
    write_line(output_stream, "Goodbye.")

    return CommandOutcome(should_exit=True)


def cell_write_arguments(args: list[str], usage: str) -> tuple[str, str, str, str]:
    require_arguments(args, 4, usage)

    return args[0], args[1], args[2], " ".join(args[3:])


def cell_location_arguments(args: list[str], usage: str) -> tuple[str, str, str]:
    require_arguments(args, 3, usage)

    return args[0], args[1], args[2]


def row_write_arguments(args: list[str], usage: str) -> tuple[str, str, dict[str, str]]:
    require_arguments(args, 3, usage)

    return args[0], args[1], parse_row_values(args[2:], usage)


def row_location_arguments(args: list[str], usage: str) -> tuple[str, str]:
    require_arguments(args, 2, usage)

    return args[0], args[1]


def one_argument(args: list[str], usage: str) -> str:
    require_arguments(args, 1, usage)

    return args[0]


def no_arguments(args: list[str], usage: str) -> None:
    if args:
        raise CliUsageError(usage)


def require_arguments(args: list[str], required_count: int, usage: str) -> None:
    if len(args) < required_count:
        raise CliUsageError(usage)


def parse_row_values(fields: list[str], usage: str) -> dict[str, str]:
    values = {}
    for field in fields:
        key, value = split_row_field(field, usage)
        values[key] = value

    return values


def split_row_field(field: str, usage: str) -> tuple[str, str]:
    if "=" not in field:
        raise CliUsageError(usage)

    key, value = field.split("=", 1)
    if not key or value == "":
        raise CliUsageError(usage)

    return key, value


def write_rows(output_stream: TextIO, rows: list[dict[str, str]]) -> None:
    if not rows:
        write_line(output_stream, "No rows found.")
        return

    for row in rows:
        write_row(output_stream, row)


def write_row(output_stream: TextIO, row: dict[str, str]) -> None:
    write_line(output_stream, " ".join(row_fields(row)))


def row_fields(row: dict[str, str]) -> list[str]:
    return [f"{key}={value}" for key, value in row.items()]


def write_line(output_stream: TextIO, message: str) -> None:
    print(message, file=output_stream)
    output_stream.flush()


COMMAND_HANDLERS = {
    "/add_cell": add_cell,
    "/get_cell": get_cell,
    "/update_cell": update_cell,
    "/remove_cell": remove_cell,
    "/add_row": add_row,
    "/get_row": get_row,
    "/update_row": update_row,
    "/remove_row": remove_row,
    "/list_rows": list_rows,
    "/clear_database": clear_database,
    "/help": show_help,
    "/exit": exit_cli,
}


if __name__ == "__main__":
    raise SystemExit(main())
