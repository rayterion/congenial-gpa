# GPA Calculator

GPA Calculator is a Python project for managing grade-style tabular data through a small in-memory database, an HTTP API, and an interactive command-line client.

The repository is currently a storage and CLI foundation rather than a finished GPA formula engine. It can create, read, update, list, and delete tables, rows, and cells that could be used to store students, courses, grades, credits, or other academic records.

## What It Includes

- In-memory table storage in `src/services/database_storage.py`
- Lightweight HTTP API in `src/services/database_api.py`
- Interactive CLI in `apps/cli_app.py`
- API client wrapper in `apps/api_client.py`
- CLI command parsing and execution in `apps/cli_commands.py`
- Unit tests with `pytest`
- Behavior tests with `behave`

## Project Structure

```text
apps/
  api_client.py       HTTP client used by the CLI
  cli_app.py          Interactive CLI entry point
  cli_commands.py     Command parser and command handlers

src/services/
  database_api.py     Local HTTP API around the storage service
  database_storage.py In-memory table, row, and cell storage

features/
  database_api_cli.feature
  steps/              Behave step definitions
  support/            Test terminal helper

tests/unit/
  test_*.py           Unit tests for storage and CLI behavior
```

## Setup

Use the project virtual environment before installing dependencies or running commands.

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.in
```

`requirements.in` contains the direct development dependencies. If you use `pip-tools`, you can generate a pinned `requirements.txt` locally:

```powershell
pip-compile
```

## Running the API

The API is usually started by the test suite. For manual CLI testing, start it in one terminal:

```powershell
.\.venv\Scripts\activate
@'
from src.services.database_api import DatabaseAPI
import time

api = DatabaseAPI(port=8000)
api.start()
print(f"Database API running at {api.get_base_url()}")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    api.stop()
'@ | python -
```

The server listens on `http://localhost:8000` by default.

## Running the CLI

With the API running, start the CLI in another terminal:

```powershell
.\.venv\Scripts\activate
python -m apps.cli_app
```

The CLI reads these optional environment variables:

- `DATABASE_API_HOST`, default: `localhost`
- `DATABASE_API_PORT`, default: `8000`

Example:

```powershell
$env:DATABASE_API_PORT = "8001"
python -m apps.cli_app
```

## CLI Commands

The CLI accepts whitespace-separated commands.

```text
/add_cell <table> <row_id> <cell> <value>
/get_cell <table> <row_id> <cell>
/update_cell <table> <row_id> <cell> <value>
/remove_cell <table> <row_id> <cell>

/add_row <table> <row_id> [key=value ...]
/get_row <table> <row_id>
/update_row <table> <row_id> [key=value ...]
/remove_row <table> <row_id>
/list_rows <table>

/clear_database
/help
/exit
```

Example session:

```text
/add_row grades 1 student=Ana course=Math credits=3 grade=A
/get_row grades 1
/update_cell grades 1 grade A-
/list_rows grades
/exit
```

Values with spaces are not currently supported by the CLI parser. Use compact values in CLI commands or call the HTTP API directly for richer JSON data.

## HTTP API

The API stores data in memory, so data is cleared when the API process stops.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health check |
| `GET` | `/` | List all tables |
| `GET` | `/{table}` | List rows in a table |
| `POST` | `/{table}/{row_id}` | Create or extend a row from a JSON body |
| `GET` | `/{table}/{row_id}` | Read a row |
| `PUT` | `/{table}/{row_id}` | Update fields in a row from a JSON body |
| `DELETE` | `/{table}/{row_id}` | Delete a row |
| `GET` | `/{table}/{row_id}/{cell}` | Read one cell |
| `PUT` | `/{table}/{row_id}/{cell}` | Set one cell using `{"value": "..."}` |
| `DELETE` | `/{table}/{row_id}/{cell}` | Delete one cell |
| `DELETE` | `/clear` | Clear all stored data |

## Running Tests

Run the unit test suite:

```powershell
.\.venv\Scripts\activate
pytest
```

Run the behavior tests:

```powershell
.\.venv\Scripts\activate
behave
```

`setup.cfg` configures pytest to use the local package paths, coverage reporting, and spec-style output.

## Current Limitations

- GPA calculation rules are not implemented yet.
- Data is stored in memory only.
- The CLI parser splits on whitespace, so quoted multi-word values are not supported.
- The API has no authentication or persistence layer.

## Possible Next Steps

- Add a GPA calculation service for course grades and credit hours.
- Add persistent storage behind `DatabaseStorage`.
- Add an API or CLI command for calculating GPA from stored grade rows.
- Improve CLI parsing for quoted values.
