from src.services.database_api import DatabaseAPI
from support import CLIMockTerminal
from scripts.dev_db import get_db_url, up_dev_db, down_dev_db

def before_all(context):
    up_dev_db()
    context.database_url = get_db_url()

    context.api_port = 8000
    context.db_api = DatabaseAPI(port=context.api_port, database_url=context.database_url)
    context.db_api.start()
    context.base_url = context.db_api.get_base_url()

    context.cli_terminal = CLIMockTerminal()

def after_all(context):
    down_dev_db()
    context.db_api.shutdown()

def after_scenario(context, scenario):
    """Ensure the CLI is closed after each scenario regardless of outcome."""
    context.cli_terminal.run_cli_command(["/clear_database", f"--db_api_url={context.base_url}"])
    context.cli_terminal.clear_logs()
