from behave import given, when, then
from subprocess import run
import requests

@when('I run the command "{command}"')
def step_run_command(context, command):
    """Run a CLI command and store the output in the context."""
    context.cli_terminal.run_cli_command(command.split())
    context.cli_output = context.cli_terminal.get_logs()[-1]
    
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
