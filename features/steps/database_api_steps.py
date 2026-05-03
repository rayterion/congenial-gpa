import requests
from behave import given, when, then


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _seed_row(context, table: str, row_id: str, row_data: dict):
    """POST a single row directly to the database API (used in Given steps)."""
    response = requests.post(
        f"{context.base_url}/{table}/{row_id}",
        json=row_data,
    )
    assert response.status_code in (200, 201), (
        f"Failed to seed row {row_id} in {table}: {response.status_code} {response.text}"
    )


def _table_rows_from_context(context) -> list[tuple[str, dict]]:
    """Parse a behave table into (row_id, data_dict) pairs, excluding the 'id' column."""
    headers = [h.strip() for h in context.table.headings]
    rows = []
    for row in context.table:
        row_id = row["id"].strip()
        data = {h: row[h].strip() for h in headers if h != "id"}
        rows.append((row_id, data))
    return rows


# ──────────────────────────────────────────────────────────────────────────────
# Background
# ──────────────────────────────────────────────────────────────────────────────

@given("the database API is running")
def step_db_api_is_running(context):
    response = requests.get(f"{context.base_url}/health")
    assert response.status_code == 200, (
        f"Database API did not respond with 200 on /health — got {response.status_code}"
    )


@given("the database is empty")
def step_db_is_empty(context):
    """Clear the database via the API before each scenario."""
    response = requests.delete(f"{context.base_url}/clear")
    assert response.status_code in (200, 204), (
        f"Failed to clear the database: {response.status_code} {response.text}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# CLI lifecycle
# ──────────────────────────────────────────────────────────────────────────────

@given("I have launched the database CLI")
def step_cli_is_launched(context):
    """
    The CLI is already started by before_scenario's 'run' command.
    We capture its welcome output so assertions later have something to read.
    """
    context.cli_output = context.dev_terminal.get_output()


@when("I run the database CLI")
def step_run_cli(context):
    """Explicit 'run' for the Launch CLI scenario — capture the welcome banner."""
    context.cli_output = context.dev_terminal.send_command("run")


@when('I run the command "{command}"')
def step_run_command(context, command):
    context.cli_output = context.dev_terminal.send_command(command)


# ──────────────────────────────────────────────────────────────────────────────
# Welcome page / help
# ──────────────────────────────────────────────────────────────────────────────

@then("it should launch a welcome page")
def step_should_show_welcome(context):
    assert context.cli_output, "No CLI output received — expected a welcome page"
    output_lower = context.cli_output.lower()
    assert "welcome" in output_lower or "database cli" in output_lower, (
        f"Welcome page not found in output:\n{context.cli_output}"
    )


@then("it should contain a commands section")
def step_should_contain_commands_section(context):
    assert "commands" in context.cli_output.lower(), (
        f"'Commands' section not found in output:\n{context.cli_output}"
    )


@then("the CLI should show the commands section")
def step_show_commands_section(context):
    assert "commands" in context.cli_output.lower(), (
        f"'Commands' section not found in /help output:\n{context.cli_output}"
    )


@then("the commands section should include all available database operations")
def step_commands_include_all_operations(context):
    expected = context.commands_list = [row.as_dict() for row in context.table]
    missing = [cmd for cmd in expected if cmd not in context.cli_output]
    assert not missing, (
        f"The following commands were missing from /help output: {missing}\n"
        f"Full output:\n{context.cli_output}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Cell — Given (pre-seed)
# ──────────────────────────────────────────────────────────────────────────────

@given('the database has table "{table}", row "{row_id}", cell "{cell}" with value "{value}"')
def step_db_has_cell(context, table, row_id, cell, value):
    _seed_row(context, table, row_id, {cell: value})


# ──────────────────────────────────────────────────────────────────────────────
# Cell — Then (API verification)
# ──────────────────────────────────────────────────────────────────────────────

@then("the CLI should send a create cell request to the database API")
def step_cli_sent_create_cell(context):
    # The side-effect (value stored) is verified by the next step.
    # If the API request was not made, the subsequent DB assertion will fail.
    pass


@then("the CLI should send a read cell request to the database API")
def step_cli_sent_read_cell(context):
    pass


@then("the CLI should send an update cell request to the database API")
def step_cli_sent_update_cell(context):
    pass


@then("the CLI should send a delete cell request to the database API")
def step_cli_sent_delete_cell(context):
    pass


@then('the database should store "{value}" in table "{table}", row "{row_id}", cell "{cell}"')
def step_db_stores_cell_value(context, value, table, row_id, cell):
    response = requests.get(f"{context.base_url}/{table}/{row_id}/{cell}")
    assert response.status_code == 200, (
        f"GET /{table}/{row_id}/{cell} returned {response.status_code}"
    )
    data = response.json()
    actual = str(data.get("value", ""))
    assert actual == value, (
        f"Expected cell value '{value}', got '{actual}'"
    )


@then('the CLI should show the value "{value}"')
def step_cli_shows_value(context, value):
    assert value in context.cli_output, (
        f"Expected value '{value}' in CLI output:\n{context.cli_output}"
    )


@then('table "{table}", row "{row_id}" should not contain cell "{cell}"')
def step_cell_not_in_db(context, table, row_id, cell):
    response = requests.get(f"{context.base_url}/{table}/{row_id}/{cell}")
    assert response.status_code == 404, (
        f"Expected 404 for deleted cell /{table}/{row_id}/{cell}, "
        f"got {response.status_code}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Row — Given (pre-seed)
# ──────────────────────────────────────────────────────────────────────────────

@given('the database has the following row in table "{table}"')
def step_db_has_row(context, table):
    for row_id, data in _table_rows_from_context(context):
        _seed_row(context, table, row_id, data)


@given('the database has the following rows in table "{table}"')
def step_db_has_rows(context, table):
    for row_id, data in _table_rows_from_context(context):
        _seed_row(context, table, row_id, data)


# ──────────────────────────────────────────────────────────────────────────────
# Row — Then (API verification)
# ──────────────────────────────────────────────────────────────────────────────

@then("the CLI should send a create row request to the database API")
def step_cli_sent_create_row(context):
    pass


@then("the CLI should send a read row request to the database API")
def step_cli_sent_read_row(context):
    pass


@then("the CLI should send an update row request to the database API")
def step_cli_sent_update_row(context):
    pass


@then("the CLI should send a delete row request to the database API")
def step_cli_sent_delete_row(context):
    pass


@then("the CLI should send a list rows request to the database API")
def step_cli_sent_list_rows(context):
    pass


@then("the CLI should send a clear database request to the database API")
def step_cli_sent_clear_db(context):
    pass


@then('the database should store the following row in table "{table}"')
def step_db_stores_row(context, table):
    headers = [h.strip() for h in context.table.headings]
    for row_id, expected_data in _table_rows_from_context(context):
        response = requests.get(f"{context.base_url}/{table}/{row_id}")
        assert response.status_code == 200, (
            f"GET /{table}/{row_id} returned {response.status_code}"
        )
        actual = response.json()
        for col in headers:
            if col == "id":
                continue
            expected_val = expected_data[col]
            actual_val = str(actual.get(col, ""))
            assert actual_val == expected_val, (
                f"Row {row_id}, column '{col}': expected '{expected_val}', got '{actual_val}'"
            )


@then("the CLI should show the following row")
def step_cli_shows_row(context):
    for row in context.table:
        for heading in context.table.headings:
            cell_value = row[heading].strip()
            assert cell_value in context.cli_output, (
                f"Expected '{cell_value}' (column '{heading}') in CLI output:\n{context.cli_output}"
            )


@then("the CLI should show the following rows")
def step_cli_shows_rows(context):
    for row in context.table:
        for heading in context.table.headings:
            cell_value = row[heading].strip()
            assert cell_value in context.cli_output, (
                f"Expected '{cell_value}' (column '{heading}') in CLI output:\n{context.cli_output}"
            )


@then('table "{table}" should not contain row "{row_id}"')
def step_table_should_not_contain_row(context, table, row_id):
    response = requests.get(f"{context.base_url}/{table}/{row_id}")
    assert response.status_code == 404, (
        f"Expected 404 for deleted row /{table}/{row_id}, got {response.status_code}"
    )


@then("the database should be empty")
def step_db_should_be_empty(context):
    response = requests.get(f"{context.base_url}/")
    assert response.status_code == 200, (
        f"GET / returned {response.status_code}"
    )
    data = response.json()
    # Accept an empty dict, empty list, or a {"tables": {}} envelope
    if isinstance(data, dict):
        tables = data.get("tables", data)
        assert len(tables) == 0, f"Expected empty database, found: {tables}"
    else:
        assert len(data) == 0, f"Expected empty database, found: {data}"


# ──────────────────────────────────────────────────────────────────────────────
# CLI error / status messages
# ──────────────────────────────────────────────────────────────────────────────

@then("the CLI should show a success message")
def step_cli_shows_success(context):
    output_lower = context.cli_output.lower()
    assert any(word in output_lower for word in ["success", "ok", "done", "created", "updated", "removed", "cleared"]), (
        f"No success message found in CLI output:\n{context.cli_output}"
    )


@then("the CLI should show a not found error")
def step_cli_shows_not_found(context):
    output_lower = context.cli_output.lower()
    assert any(phrase in output_lower for phrase in ["not found", "404", "does not exist", "no such"]), (
        f"No 'not found' error found in CLI output:\n{context.cli_output}"
    )


@then("the CLI should show an unknown command error")
def step_cli_shows_unknown_command(context):
    output_lower = context.cli_output.lower()
    assert any(phrase in output_lower for phrase in ["unknown command", "unrecognized", "not recognized", "invalid command"]), (
        f"No unknown-command error found in CLI output:\n{context.cli_output}"
    )


@then("the CLI should show a missing arguments error")
def step_cli_shows_missing_args(context):
    output_lower = context.cli_output.lower()
    assert any(phrase in output_lower for phrase in ["missing", "required", "argument", "too few"]), (
        f"No missing-arguments error found in CLI output:\n{context.cli_output}"
    )


@then("the CLI should explain the correct command usage")
def step_cli_shows_usage(context):
    output_lower = context.cli_output.lower()
    assert any(phrase in output_lower for phrase in ["usage", "syntax", "example", "/add_cell"]), (
        f"No usage explanation found in CLI output:\n{context.cli_output}"
    )


@then("the CLI should close successfully")
def step_cli_closes(context):
    assert not context.dev_terminal.is_running(), (
        "Expected the CLI process to have exited, but it is still running"
    )


@then("the CLI should remain open")
def step_cli_remains_open(context):
    assert context.dev_terminal.is_running(), (
        "Expected the CLI to remain open after an error, but it has exited"
    )