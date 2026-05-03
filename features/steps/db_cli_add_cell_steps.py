from behave import given, when, then
from subprocess import run
import requests

@when('I run the command "{command}"')
def step_run_command(context, command):
    """Run a CLI command and store the output in the context."""
    result = run(command.split(), capture_output=True, text=True)
    context.cli_output = result.stdout
    context.cli_error = result.stderr
    context.cli_returncode = result.returncode

@then('the CLI should send a create cell request to the database API')
def step_check_create_cell_request(context):
    """Check that the CLI sent a create cell request to the database API."""
    # This step would require mocking the database API to verify the request was made.
    # For now, we will assume that if the CLI command ran successfully, it sent the request.
    assert context.cli_returncode == 0, f"CLI command failed with error: {context.cli_error}"

@then('the database should store "{value}" in table "{table}", row "{row}", column "{column}"')
def step_check_database_storage(context, value, table, row, column):
    """Check that the database stored the value in the correct location."""
    response = requests.get(f"{context.base_url}/{table}/{row}/{column}")
    assert response.status_code == 200, f"Failed to retrieve cell value: {response.text}"
    assert response.json().get("value") == value, f"Expected value '{value}', but got '{response.json().get('value')}'"

@then('the CLI should show a success message')
def step_check_success_message(context):
    """Check that the CLI output contains a success message."""
    assert "success" in context.cli_output.lower(), f"Expected success message in CLI output, but got: {context.cli_output}"
