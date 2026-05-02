from io import StringIO

import database_api
from database_api import DatabaseApiClient, DatabaseValueNotFoundError
from database_api_cli import AVAILABLE_COMMANDS, execute_command, print_welcome_page


class StubResponse:
    def __init__(self, status_code=200, body=None):
        self.status_code = status_code
        self.body = body or {}

    def json(self):
        return self.body


class RecordingClient:
    def __init__(self):
        self.calls = []

    def create_cell(self, table, row, cell, value):
        self.calls.append(("create_cell", table, row, cell, value))

    def update_row(self, table, row, values):
        self.calls.append(("update_row", table, row, values))


class MissingCellClient:
    def read_cell(self, table, row, cell):
        raise DatabaseValueNotFoundError("Not found")


def test_welcome_page_lists_available_commands():
    output = StringIO()

    print_welcome_page(output)

    rendered_output = output.getvalue()
    assert "Welcome" in rendered_output
    assert "Commands" in rendered_output
    for command in AVAILABLE_COMMANDS:
        assert command in rendered_output


def test_add_cell_command_sends_cell_arguments_to_client():
    output = StringIO()
    client = RecordingClient()

    outcome = execute_command("/add_cell users 1 name Martin", client, output)

    assert not outcome.should_exit
    assert client.calls == [("create_cell", "users", "1", "name", "Martin")]
    assert "Success" in output.getvalue()


def test_update_row_command_sends_parsed_row_fields_to_client():
    output = StringIO()
    client = RecordingClient()

    outcome = execute_command(
        "/update_row users 1 name=Tulio age=21 role=engineer",
        client,
        output,
    )

    assert not outcome.should_exit
    assert client.calls == [
        (
            "update_row",
            "users",
            "1",
            {"name": "Tulio", "age": "21", "role": "engineer"},
        )
    ]
    assert "Success" in output.getvalue()


def test_unknown_and_missing_argument_errors_keep_cli_running():
    client = RecordingClient()
    output = StringIO()

    unknown_outcome = execute_command("/unknown_command", client, output)
    missing_outcome = execute_command("/add_cell users 1", client, output)

    rendered_output = output.getvalue()
    assert not unknown_outcome.should_exit
    assert not missing_outcome.should_exit
    assert "Unknown command" in rendered_output
    assert "Missing arguments" in rendered_output
    assert "Usage: /add_cell" in rendered_output


def test_api_client_builds_cell_request(monkeypatch):
    calls = []

    def fake_request(method, url, json, timeout):
        calls.append((method, url, json, timeout))
        return StubResponse(status_code=201)

    monkeypatch.setattr(database_api.requests, "request", fake_request)

    client = DatabaseApiClient("http://api.test/")
    client.create_cell("users", "1", "name", "Martin")

    assert calls == [
        (
            "POST",
            "http://api.test/tables/users/rows/1/cells/name",
            {"value": "Martin"},
            3.0,
        )
    ]


def test_api_client_builds_row_request(monkeypatch):
    calls = []

    def fake_request(method, url, json, timeout):
        calls.append((method, url, json, timeout))
        return StubResponse(status_code=200)

    monkeypatch.setattr(database_api.requests, "request", fake_request)

    client = DatabaseApiClient("http://api.test")
    client.update_row("users", "1", {"name": "Tulio", "age": "21"})

    assert calls == [
        (
            "PUT",
            "http://api.test/tables/users/rows/1",
            {"name": "Tulio", "age": "21"},
            3.0,
        )
    ]


def test_not_found_response_is_visible_to_user():
    output = StringIO()

    outcome = execute_command("/get_cell users 1 name", MissingCellClient(), output)

    assert not outcome.should_exit
    assert "Not found" in output.getvalue()
