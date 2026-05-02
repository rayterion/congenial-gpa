import os
import subprocess
import sys
import threading
import time

from behave import given, then, when


AVAILABLE_COMMANDS = [
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

CELL_OPERATION_BY_ACTION = {
    "create": "create_cell",
    "read": "read_cell",
    "update": "update_cell",
    "delete": "delete_cell",
}

ROW_OPERATION_BY_ACTION = {
    "create": "create_row",
    "read": "read_row",
    "update": "update_row",
    "delete": "delete_row",
}


@given("the database API is running")
def step_database_api_is_running(context):
    assert context.fake_api.is_running(), "Expected the fake database API to be running."


@given("the database is empty")
def step_database_is_empty(context):
    context.fake_api.clear_database()
    assert context.fake_api.is_database_empty(), "Expected the fake database to be empty."


@given('I have launched the database CLI')
def step_i_have_launched_the_database_cli(context):
    launch_database_cli(context)


@given('the database has table "{table}", row "{row}", cell "{cell}" with value "{value}"')
def step_database_has_cell(context, table, row, cell, value):
    context.fake_api.store_cell(table, row, cell, value)


@given('the database has the following row in table "{table}":')
def step_database_has_row(context, table):
    row = single_table_row(context)
    context.fake_api.store_row(table, row["id"], row)


@given('the database has the following rows in table "{table}":')
def step_database_has_rows(context, table):
    for row in table_rows(context):
        context.fake_api.store_row(table, row["id"], row)


@when("I run the database CLI")
def step_i_run_the_database_cli(context):
    launch_database_cli(context)


@when('I run the command "{command}"')
def step_i_run_the_command(context, command):
    run_cli_command(context, command)


@then("it should launch a welcome page")
def step_it_should_launch_welcome_page(context):
    wait_for_cli_output(
        context,
        "welcome page",
        lambda output: "welcome" in output.lower(),
    )


@then("it should contain a commands section")
def step_it_should_contain_commands_section(context):
    assert_commands_section_is_visible(context, recent=False)


@then("the commands section should include /add_cell")
def step_commands_section_includes_add_cell(context):
    assert_command_is_visible(context, "/add_cell")


@then("the commands section should include /get_cell")
def step_commands_section_includes_get_cell(context):
    assert_command_is_visible(context, "/get_cell")


@then("the commands section should include /update_cell")
def step_commands_section_includes_update_cell(context):
    assert_command_is_visible(context, "/update_cell")


@then("the commands section should include /remove_cell")
def step_commands_section_includes_remove_cell(context):
    assert_command_is_visible(context, "/remove_cell")


@then("the commands section should include /add_row")
def step_commands_section_includes_add_row(context):
    assert_command_is_visible(context, "/add_row")


@then("the commands section should include /get_row")
def step_commands_section_includes_get_row(context):
    assert_command_is_visible(context, "/get_row")


@then("the commands section should include /update_row")
def step_commands_section_includes_update_row(context):
    assert_command_is_visible(context, "/update_row")


@then("the commands section should include /remove_row")
def step_commands_section_includes_remove_row(context):
    assert_command_is_visible(context, "/remove_row")


@then("the commands section should include /list_rows")
def step_commands_section_includes_list_rows(context):
    assert_command_is_visible(context, "/list_rows")


@then("the commands section should include /clear_database")
def step_commands_section_includes_clear_database(context):
    assert_command_is_visible(context, "/clear_database")


@then("the commands section should include /help")
def step_commands_section_includes_help(context):
    assert_command_is_visible(context, "/help")


@then("the commands section should include /exit")
def step_commands_section_includes_exit(context):
    assert_command_is_visible(context, "/exit")


@then("the commands section should include all available database operations")
def step_commands_section_includes_all_operations(context):
    output = assert_commands_section_is_visible(context, recent=True)
    missing_commands = [
        command for command in AVAILABLE_COMMANDS if command not in output
    ]
    assert not missing_commands, f"Missing commands from help output: {missing_commands}"


@then("the CLI should show the commands section")
def step_cli_should_show_commands_section(context):
    assert_commands_section_is_visible(context, recent=True)


@then("the CLI should send a {action} cell request to the database API")
@then("the CLI should send an {action} cell request to the database API")
def step_cli_should_send_cell_request(context, action):
    assert_api_operation_was_sent(context, CELL_OPERATION_BY_ACTION[action])


@then("the CLI should send a {action} row request to the database API")
@then("the CLI should send an {action} row request to the database API")
def step_cli_should_send_row_request(context, action):
    assert_api_operation_was_sent(context, ROW_OPERATION_BY_ACTION[action])


@then("the CLI should send a list rows request to the database API")
def step_cli_should_send_list_rows_request(context):
    assert_api_operation_was_sent(context, "list_rows")


@then("the CLI should send a clear database request to the database API")
def step_cli_should_send_clear_database_request(context):
    assert_api_operation_was_sent(context, "clear_database")


@then('the database should store "{value}" in table "{table}", row "{row}", cell "{cell}"')
def step_database_should_store_cell(context, value, table, row, cell):
    stored_value = context.fake_api.get_cell(table, row, cell)
    assert stored_value == value, f"Expected {value!r}, got {stored_value!r}."


@then('table "{table}", row "{row}" should not contain cell "{cell}"')
def step_row_should_not_contain_cell(context, table, row, cell):
    assert not context.fake_api.has_cell(table, row, cell)


@then('the database should store the following row in table "{table}":')
def step_database_should_store_row(context, table):
    expected_row = single_table_row(context)
    stored_row = context.fake_api.get_row(table, expected_row["id"])
    assert stored_row == expected_row, f"Expected {expected_row!r}, got {stored_row!r}."


@then('table "{table}" should not contain row "{row}"')
def step_table_should_not_contain_row(context, table, row):
    assert not context.fake_api.has_row(table, row)


@then("the database should be empty")
def step_database_should_be_empty(context):
    assert context.fake_api.is_database_empty(), "Expected the fake database to be empty."


@then("the CLI should show a success message")
def step_cli_should_show_success_message(context):
    wait_for_recent_cli_output(
        context,
        "success message",
        output_contains_any(
            "success",
            "successful",
            "created",
            "updated",
            "deleted",
            "removed",
            "cleared",
            "ok",
        ),
    )


@then('the CLI should show the value "{value}"')
def step_cli_should_show_value(context, value):
    wait_for_recent_cli_output(
        context,
        f"value {value!r}",
        lambda output: value in output,
    )


@then("the CLI should show the following row:")
def step_cli_should_show_row(context):
    assert_cli_output_contains_rows(context, [single_table_row(context)])


@then("the CLI should show the following rows:")
def step_cli_should_show_rows(context):
    assert_cli_output_contains_rows(context, table_rows(context))


@then("the CLI should close successfully")
def step_cli_should_close_successfully(context):
    process = context.cli_process
    assert process is not None, "Expected a CLI process to be available."

    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        fail_with_cli_output(context, "Expected the CLI to close after /exit.")

    assert process.returncode == 0, (
        f"Expected the CLI to exit with code 0, got {process.returncode}.\n"
        f"CLI output:\n{cli_output(context)}"
    )


@then("the CLI should show an unknown command error")
def step_cli_should_show_unknown_command_error(context):
    wait_for_recent_cli_output(
        context,
        "unknown command error",
        output_contains_all("unknown", "command"),
    )


@then("the CLI should remain open")
def step_cli_should_remain_open(context):
    time.sleep(0.2)
    assert_cli_is_running(context)


@then("the CLI should show a missing arguments error")
def step_cli_should_show_missing_arguments_error(context):
    wait_for_recent_cli_output(
        context,
        "missing arguments error",
        output_contains_any("missing", "required", "argument"),
    )


@then("the CLI should explain the correct command usage")
def step_cli_should_explain_correct_usage(context):
    wait_for_recent_cli_output(
        context,
        "command usage",
        lambda output: "/add_cell" in output and text_contains_any(
            output,
            "usage",
            "format",
            "syntax",
            "table",
            "row",
            "cell",
        ),
    )


@then("the CLI should show a not found error")
def step_cli_should_show_not_found_error(context):
    wait_for_recent_cli_output(
        context,
        "not found error",
        lambda output: "not found" in output.lower()
        or "does not exist" in output.lower(),
    )


def launch_database_cli(context):
    if is_cli_running(context):
        return

    command = cli_command(context)
    context.cli_process = subprocess.Popen(
        command,
        cwd=context.project_root,
        env=cli_environment(context),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )
    start_cli_output_reader(context)
    assert_cli_did_not_exit_immediately(context)


def cli_command(context):
    return [
        python_executable(context),
        str(context.project_root / "src" / "database_api_cli.py"),
    ]


def python_executable(context):
    venv_python = context.project_root / ".venv" / "Scripts" / "python.exe"
    if venv_python.exists():
        return str(venv_python)

    return sys.executable


def cli_environment(context):
    environment = os.environ.copy()
    environment["DATABASE_API_BASE_URL"] = context.api_base_url
    environment["PYTHONUNBUFFERED"] = "1"
    environment["PYTHONPATH"] = python_path_for_cli(context, environment)

    return environment


def python_path_for_cli(context, environment):
    paths = [str(context.project_root), str(context.project_root / "src")]
    existing_python_path = environment.get("PYTHONPATH")
    if existing_python_path:
        paths.append(existing_python_path)

    return os.pathsep.join(paths)


def start_cli_output_reader(context):
    context.cli_reader_thread = threading.Thread(
        target=read_cli_output,
        args=(context, context.cli_process),
        daemon=True,
    )
    context.cli_reader_thread.start()


def read_cli_output(context, process):
    if process.stdout is None:
        return

    while True:
        character = process.stdout.read(1)
        if character == "":
            return

        append_cli_output(context, character)


def append_cli_output(context, character):
    with context.cli_output_lock:
        context.cli_output += character


def assert_cli_did_not_exit_immediately(context):
    time.sleep(0.2)
    if context.cli_process.poll() is None:
        return

    time.sleep(0.1)
    fail_with_cli_output(context, "Expected the database CLI to keep running.")


def run_cli_command(context, command):
    assert_cli_is_running(context)
    context.last_command = command
    context.last_command_output_index = len(cli_output(context))
    context.last_command_request_count = context.fake_api.request_count()

    try:
        context.cli_process.stdin.write(f"{command}\n")
        context.cli_process.stdin.flush()
    except OSError as error:
        raise AssertionError(f"Failed to send command to CLI: {error}") from error


def is_cli_running(context):
    process = getattr(context, "cli_process", None)
    return process is not None and process.poll() is None


def assert_cli_is_running(context):
    if is_cli_running(context):
        return

    fail_with_cli_output(context, "Expected the CLI to remain open.")


def assert_api_operation_was_sent(context, operation):
    request = context.fake_api.wait_for_operation(
        operation,
        context.last_command_request_count,
    )
    if request is not None:
        return

    captured_operations = context.fake_api.captured_operations()
    raise AssertionError(
        f"Expected API operation {operation!r}. "
        f"Captured operations: {captured_operations!r}.\n"
        f"CLI output:\n{cli_output(context)}"
    )


def assert_commands_section_is_visible(context, recent):
    return wait_for_cli_output(
        context,
        "commands section",
        lambda output: "commands" in output.lower(),
        recent=recent,
    )


def assert_command_is_visible(context, command):
    wait_for_cli_output(
        context,
        f"command {command}",
        lambda output: command in output,
    )


def assert_cli_output_contains_rows(context, rows):
    wait_for_recent_cli_output(
        context,
        "table rows",
        lambda output: all(row_is_visible(output, row) for row in rows),
    )


def row_is_visible(output, row):
    return all(str(value) in output for value in row.values())


def wait_for_recent_cli_output(context, description, predicate):
    return wait_for_cli_output(context, description, predicate, recent=True)


def wait_for_cli_output(context, description, predicate, recent=False, timeout=3):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        output = relevant_cli_output(context, recent)
        if predicate(output):
            return output

        time.sleep(0.05)

    fail_with_cli_output(context, f"Expected CLI output to include {description}.")


def relevant_cli_output(context, recent):
    if recent:
        return recent_cli_output(context)

    return cli_output(context)


def recent_cli_output(context):
    return cli_output(context)[context.last_command_output_index :]


def cli_output(context):
    with context.cli_output_lock:
        return context.cli_output


def output_contains_any(*expected_values):
    return lambda output: text_contains_any(output, *expected_values)


def output_contains_all(*expected_values):
    return lambda output: text_contains_all(output, *expected_values)


def text_contains_any(output, *expected_values):
    normalized_output = output.lower()

    return any(value.lower() in normalized_output for value in expected_values)


def text_contains_all(output, *expected_values):
    normalized_output = output.lower()

    return all(value.lower() in normalized_output for value in expected_values)


def table_rows(context):
    return [
        {heading: row[heading] for heading in context.table.headings}
        for row in context.table.rows
    ]


def single_table_row(context):
    rows = table_rows(context)
    assert len(rows) == 1, f"Expected one table row, got {len(rows)}."

    return rows[0]


def fail_with_cli_output(context, message):
    raise AssertionError(f"{message}\nCLI output:\n{cli_output(context)}")
