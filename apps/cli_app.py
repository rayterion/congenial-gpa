"""Database CLI application.

Run as:  python -m apps.cli_app
"""
import os
import sys

from apps.api_client import ApiClient
from apps.cli_commands import execute_command, COMMANDS


cli_app = None  # module-level sentinel imported by environment.py


def run_cli_app() -> None:
    base_url = _get_api_base_url()
    api = ApiClient(base_url)
    _print_welcome_banner()
    _run_command_loop(api)


def _get_api_base_url() -> str:
    port = os.environ.get("DATABASE_API_PORT", "8000")
    host = os.environ.get("DATABASE_API_HOST", "localhost")
    return f"http://{host}:{port}"


def _print_welcome_banner() -> None:
    print("Welcome to the Database CLI!")
    print()
    print("Commands:")
    for cmd in COMMANDS:
        print(f"  {cmd}")
    print()
    sys.stdout.flush()


def _run_command_loop(api: ApiClient) -> None:
    for line in sys.stdin:
        command_text = line.strip()
        if not command_text:
            continue
        if command_text == "/exit":
            _handle_exit()
            return
        output = execute_command(command_text, api)
        print(output)
        sys.stdout.flush()


def _handle_exit() -> None:
    print("Goodbye!")
    sys.stdout.flush()


if __name__ == "__main__":
    run_cli_app()
