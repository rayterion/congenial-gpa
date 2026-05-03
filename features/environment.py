from src.services.database_api import DatabaseAPI
from apps.cli_app import cli_app
from subprocess import Popen, PIPE, run
from scripts import DevDatabase
from support import CLIMockTerminal

def before_all(context):
    context.dev_db = DevDatabase()
    context.dev_db.run()
    context.database_url = context.dev_db.get_db_url()

    context.api_port = 8000
    context.db_api = DatabaseAPI(port=context.api_port, database_url=context.database_url)
    context.db_api.start()
    context.base_url = context.db_api.get_base_url()

    context.cli_terminal = CLIMockTerminal()

def after_all(context):
    context.dev_db.shutdown()
    context.db_api.shutdown()

def after_scenario(context, scenario):
    """Ensure the CLI is closed after each scenario regardless of outcome."""
    context.cli_terminal.run_cli_command(["/clear_database", f"--db_api_url={context.base_url}"])
    context.cli_terminal.clear_logs()
