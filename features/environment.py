import json
import subprocess
import threading
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


@dataclass(frozen=True)
class CapturedRequest:
    operation: str
    method: str
    path: str
    table: str | None = None
    row: str | None = None
    cell: str | None = None
    payload: dict | None = None


class FakeDatabase:
    def __init__(self):
        self.tables = {}

    def clear(self):
        self.tables.clear()

    def is_empty(self):
        return all(not rows for rows in self.tables.values())

    def store_cell(self, table, row, cell, value):
        stored_row = self._ensure_row(table, row)
        stored_row[cell] = str(value)

    def get_cell(self, table, row, cell):
        if not self.has_cell(table, row, cell):
            raise KeyError(cell)

        return self.tables[table][row][cell]

    def remove_cell(self, table, row, cell):
        if self.has_cell(table, row, cell):
            del self.tables[table][row][cell]

    def store_row(self, table, row, values):
        self._ensure_table(table)[row] = self._normalize_row(row, values)

    def get_row(self, table, row):
        if not self.has_row(table, row):
            raise KeyError(row)

        return dict(self.tables[table][row])

    def remove_row(self, table, row):
        self._ensure_table(table).pop(row, None)

    def list_rows(self, table):
        return [dict(row) for row in self._ensure_table(table).values()]

    def has_row(self, table, row):
        return table in self.tables and row in self.tables[table]

    def has_cell(self, table, row, cell):
        return self.has_row(table, row) and cell in self.tables[table][row]

    def _ensure_table(self, table):
        return self.tables.setdefault(table, {})

    def _ensure_row(self, table, row):
        return self._ensure_table(table).setdefault(row, {"id": row})

    def _normalize_row(self, row, values):
        normalized = {key: str(value) for key, value in values.items()}
        normalized["id"] = row

        return normalized


class FakeDatabaseApiServer:
    def __init__(self):
        self.database = FakeDatabase()
        self.requests = []
        self._condition = threading.Condition()
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), self._build_handler())
        self._thread = None
        self.base_url = self._build_base_url()

    def start(self):
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        self._server.shutdown()
        self._server.server_close()
        if self._thread:
            self._thread.join(timeout=2)

    def reset(self):
        with self._condition:
            self.database.clear()
            self.requests.clear()
            self._condition.notify_all()

    def is_running(self):
        return self._thread is not None and self._thread.is_alive()

    def clear_database(self):
        with self._condition:
            self.database.clear()

    def is_database_empty(self):
        with self._condition:
            return self.database.is_empty()

    def store_cell(self, table, row, cell, value):
        with self._condition:
            self.database.store_cell(table, row, cell, value)

    def get_cell(self, table, row, cell):
        with self._condition:
            return self.database.get_cell(table, row, cell)

    def has_cell(self, table, row, cell):
        with self._condition:
            return self.database.has_cell(table, row, cell)

    def store_row(self, table, row, values):
        with self._condition:
            self.database.store_row(table, row, values)

    def get_row(self, table, row):
        with self._condition:
            return self.database.get_row(table, row)

    def has_row(self, table, row):
        with self._condition:
            return self.database.has_row(table, row)

    def request_count(self):
        with self._condition:
            return len(self.requests)

    def wait_for_operation(self, operation, after_index, timeout=3):
        with self._condition:
            self._condition.wait_for(
                lambda: self._find_operation(operation, after_index) is not None,
                timeout=timeout,
            )

            return self._find_operation(operation, after_index)

    def captured_operations(self):
        with self._condition:
            return [request.operation for request in self.requests]

    def handle_request(self, handler):
        request = self._build_request(handler)
        status, body = self._route_request(request)
        self._send_json(handler, status, body)

    def _build_handler(self):
        server = self

        class FakeDatabaseApiRequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                server.handle_request(self)

            def do_POST(self):
                server.handle_request(self)

            def do_PUT(self):
                server.handle_request(self)

            def do_DELETE(self):
                server.handle_request(self)

            def log_message(self, _format, *args):
                return

        return FakeDatabaseApiRequestHandler

    def _build_base_url(self):
        host, port = self._server.server_address
        return f"http://{host}:{port}"

    def _build_request(self, handler):
        parsed_path = urlsplit(handler.path)
        segments = [
            unquote(segment)
            for segment in parsed_path.path.strip("/").split("/")
            if segment
        ]

        return {
            "method": handler.command,
            "path": parsed_path.path,
            "segments": segments,
            "payload": self._read_json_body(handler),
        }

    def _read_json_body(self, handler):
        content_length = int(handler.headers.get("Content-Length", "0") or 0)
        if content_length == 0:
            return {}

        body = handler.rfile.read(content_length).decode("utf-8")
        if not body.strip():
            return {}

        parsed_body = json.loads(body)
        if isinstance(parsed_body, dict):
            return parsed_body

        return {"value": parsed_body}

    def _route_request(self, request):
        if self._is_cell_route(request):
            return self._handle_cell_route(request)

        if self._is_row_route(request):
            return self._handle_row_route(request)

        if self._is_rows_route(request):
            return self._handle_rows_route(request)

        if self._is_database_route(request):
            return self._handle_database_route(request)

        return 404, {"error": "Not found"}

    def _is_cell_route(self, request):
        return (
            len(request["segments"]) == 6
            and request["segments"][0] == "tables"
            and request["segments"][2] == "rows"
            and request["segments"][4] == "cells"
        )

    def _is_row_route(self, request):
        return (
            len(request["segments"]) == 4
            and request["segments"][0] == "tables"
            and request["segments"][2] == "rows"
        )

    def _is_rows_route(self, request):
        return (
            len(request["segments"]) == 3
            and request["segments"][0] == "tables"
            and request["segments"][2] == "rows"
        )

    def _is_database_route(self, request):
        return len(request["segments"]) == 1 and request["segments"][0] == "database"

    def _handle_cell_route(self, request):
        table, row, cell = request["segments"][1], request["segments"][3], request["segments"][5]
        operation = self._cell_operation_for(request["method"])
        if operation is None:
            return 405, {"error": "Method not allowed"}

        with self._condition:
            status, body = self._apply_cell_operation(operation, table, row, cell, request["payload"])
            self._capture_request(request, operation, table=table, row=row, cell=cell)

            return status, body

    def _handle_row_route(self, request):
        table, row = request["segments"][1], request["segments"][3]
        operation = self._row_operation_for(request["method"])
        if operation is None:
            return 405, {"error": "Method not allowed"}

        with self._condition:
            status, body = self._apply_row_operation(operation, table, row, request["payload"])
            self._capture_request(request, operation, table=table, row=row)

            return status, body

    def _handle_rows_route(self, request):
        table = request["segments"][1]
        if request["method"] != "GET":
            return 405, {"error": "Method not allowed"}

        with self._condition:
            rows = self.database.list_rows(table)
            self._capture_request(request, "list_rows", table=table)

            return 200, {"rows": rows}

    def _handle_database_route(self, request):
        if request["method"] != "DELETE":
            return 405, {"error": "Method not allowed"}

        with self._condition:
            self.database.clear()
            self._capture_request(request, "clear_database")

            return 200, {"status": "success"}

    def _cell_operation_for(self, method):
        return {
            "POST": "create_cell",
            "GET": "read_cell",
            "PUT": "update_cell",
            "DELETE": "delete_cell",
        }.get(method)

    def _row_operation_for(self, method):
        return {
            "POST": "create_row",
            "GET": "read_row",
            "PUT": "update_row",
            "DELETE": "delete_row",
        }.get(method)

    def _apply_cell_operation(self, operation, table, row, cell, payload):
        if operation in {"create_cell", "update_cell"}:
            value = self._cell_value_from(payload)
            self.database.store_cell(table, row, cell, value)

            return 201 if operation == "create_cell" else 200, {"value": value}

        if operation == "read_cell":
            return self._read_cell(table, row, cell)

        self.database.remove_cell(table, row, cell)

        return 200, {"status": "success"}

    def _apply_row_operation(self, operation, table, row, payload):
        if operation in {"create_row", "update_row"}:
            values = self._row_values_from(payload)
            self.database.store_row(table, row, values)

            return 201 if operation == "create_row" else 200, {"row": self.database.get_row(table, row)}

        if operation == "read_row":
            return self._read_row(table, row)

        self.database.remove_row(table, row)

        return 200, {"status": "success"}

    def _read_cell(self, table, row, cell):
        try:
            return 200, {"value": self.database.get_cell(table, row, cell)}
        except KeyError:
            return 404, {"error": "Not found"}

    def _read_row(self, table, row):
        try:
            return 200, {"row": self.database.get_row(table, row)}
        except KeyError:
            return 404, {"error": "Not found"}

    def _cell_value_from(self, payload):
        return str(payload.get("value", ""))

    def _row_values_from(self, payload):
        if isinstance(payload.get("row"), dict):
            return payload["row"]

        return payload

    def _capture_request(self, request, operation, table=None, row=None, cell=None):
        self.requests.append(
            CapturedRequest(
                operation=operation,
                method=request["method"],
                path=request["path"],
                table=table,
                row=row,
                cell=cell,
                payload=request["payload"],
            )
        )
        self._condition.notify_all()

    def _find_operation(self, operation, after_index):
        for request in self.requests[after_index:]:
            if request.operation == operation:
                return request

        return None

    def _send_json(self, handler, status, body):
        encoded_body = json.dumps(body).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(encoded_body)))
        handler.end_headers()
        handler.wfile.write(encoded_body)


def before_all(context):
    context.project_root = Path(__file__).resolve().parents[1]
    context.fake_api = FakeDatabaseApiServer()
    context.fake_api.start()
    context.api_base_url = context.fake_api.base_url


def before_scenario(context, _scenario):
    context.fake_api.reset()
    context.cli_process = None
    context.cli_output = ""
    context.cli_output_lock = threading.Lock()
    context.cli_reader_thread = None
    context.last_command = None
    context.last_command_output_index = 0
    context.last_command_request_count = 0


def after_scenario(context, _scenario):
    stop_cli_process(context)
    join_cli_reader_thread(context)


def after_all(context):
    if hasattr(context, "fake_api"):
        context.fake_api.stop()


def stop_cli_process(context):
    process = getattr(context, "cli_process", None)
    if process is None:
        return

    if process.poll() is None:
        close_process_input(process)
        terminate_process(process)

    context.cli_process = None


def close_process_input(process):
    if process.stdin is None:
        return

    try:
        process.stdin.close()
    except OSError:
        return


def terminate_process(process):
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def join_cli_reader_thread(context):
    thread = getattr(context, "cli_reader_thread", None)
    if thread is None:
        return

    thread.join(timeout=2)
