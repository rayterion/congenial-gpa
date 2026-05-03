"""HTTP REST API server wrapping DatabaseStorage."""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from src.services.database_storage import DatabaseStorage


class DatabaseAPI:
    def __init__(self, port: int = 8000, database_url: str = "") -> None:
        self._port = port
        self._storage = DatabaseStorage()
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._server = _build_server(self._port, self._storage)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()

    def get_base_url(self) -> str:
        return f"http://localhost:{self._port}"


# ──────────────────────────────────────────────────────────────────────────────
# HTTP server plumbing
# ──────────────────────────────────────────────────────────────────────────────

def _build_server(port: int, storage: DatabaseStorage) -> HTTPServer:
    handler_class = _make_handler_class(storage)
    return HTTPServer(("localhost", port), handler_class)


def _make_handler_class(storage: DatabaseStorage):
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            _handle_get(self, storage)

        def do_POST(self):
            _handle_post(self, storage)

        def do_PUT(self):
            _handle_put(self, storage)

        def do_DELETE(self):
            _handle_delete(self, storage)

        def log_message(self, fmt, *args):  # silence request logs
            pass

    return _Handler


# ──────────────────────────────────────────────────────────────────────────────
# Request dispatchers
# ──────────────────────────────────────────────────────────────────────────────

def _handle_get(handler, storage: DatabaseStorage) -> None:
    parts = _path_parts(handler.path)

    if parts == ["health"]:
        return _send_json(handler, 200, {"status": "ok"})

    if parts == []:
        return _send_json(handler, 200, {"tables": storage.list_tables()})

    if len(parts) == 1:
        table = parts[0]
        return _send_json(handler, 200, storage.list_rows(table))

    if len(parts) == 2:
        table, row_id = parts
        row = storage.get_row(table, row_id)
        if row is None:
            return _send_json(handler, 404, {"error": "not found"})
        return _send_json(handler, 200, row)

    if len(parts) == 3:
        table, row_id, cell = parts
        value = storage.get_cell(table, row_id, cell)
        if value is None:
            return _send_json(handler, 404, {"error": "not found"})
        return _send_json(handler, 200, {"value": value})

    _send_json(handler, 404, {"error": "not found"})


def _handle_post(handler, storage: DatabaseStorage) -> None:
    parts = _path_parts(handler.path)
    if len(parts) != 2:
        return _send_json(handler, 400, {"error": "expected /{table}/{row_id}"})

    table, row_id = parts
    body = _read_json_body(handler)
    storage.add_row(table, row_id, body)
    _send_json(handler, 201, {"ok": True})


def _handle_put(handler, storage: DatabaseStorage) -> None:
    parts = _path_parts(handler.path)
    body = _read_json_body(handler)

    if len(parts) == 2:
        table, row_id = parts
        storage.update_row(table, row_id, body)
        return _send_json(handler, 200, {"ok": True})

    if len(parts) == 3:
        table, row_id, cell = parts
        value = body.get("value", "")
        storage.set_cell(table, row_id, cell, value)
        return _send_json(handler, 200, {"ok": True})

    _send_json(handler, 400, {"error": "bad path"})


def _handle_delete(handler, storage: DatabaseStorage) -> None:
    parts = _path_parts(handler.path)

    if parts == ["clear"]:
        storage.clear()
        return _send_json(handler, 200, {"ok": True})

    if len(parts) == 2:
        table, row_id = parts
        storage.delete_row(table, row_id)
        return _send_json(handler, 200, {"ok": True})

    if len(parts) == 3:
        table, row_id, cell = parts
        storage.delete_cell(table, row_id, cell)
        return _send_json(handler, 200, {"ok": True})

    _send_json(handler, 400, {"error": "bad path"})


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _path_parts(raw_path: str) -> list[str]:
    path = urlparse(raw_path).path
    return [p for p in path.split("/") if p]


def _read_json_body(handler) -> dict:
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    return json.loads(handler.rfile.read(length))


def _send_json(handler, status: int, body: dict) -> None:
    payload = json.dumps(body).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)
