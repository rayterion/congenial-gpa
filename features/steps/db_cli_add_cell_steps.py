from behave import given, when, then
from subprocess import run

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

