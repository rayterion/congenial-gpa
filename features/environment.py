from src.services.database_api import DatabaseAPI
from apps.cli_app import cli_app
from .support import DevTerminal
from scripts import DevDatabase

def before_all(context):
    context.dev_terminal = DevTerminal()

    context.dev_db = DevDatabase()
    context.dev_db.run()
    context.database_url = context.dev_db.get_db_url()

    context.api_port = 8000
    context.db_api = DatabaseAPI(port=context.api_port, database_url=context.database_url)
    context.db_api.start()
    context.base_url = context.db_api.get_base_url()

    context.dev_terminal.send_command("run")

def after_all(context):
    context.dev_db.shutdown()

def before_scenario(context, scenario):
    context.dev_terminal.send_command("run")

def after_scenario(context, scenario):
    """Ensure the CLI is closed after each scenario regardless of outcome."""
    context.dev_terminal.send_command("/clear_database")
    context.dev_terminal.send_command("/exit")
