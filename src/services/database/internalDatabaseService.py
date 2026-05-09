from __future__ import annotations

from threading import Thread
from typing import Any

from flask import Flask, Response, jsonify, request
from werkzeug.serving import BaseWSGIServer, make_server

from .inMemoDb import InMemoryDatabase


class InternalDatabaseService:
    """
    Small internal HTTP API for the in-memory database.

    Supported endpoints:
        GET  /              -> health check
        POST /              -> run operation from query parameters
        GET  /operation     -> run operation from query parameters
        POST /operation     -> run operation from query parameters
        POST /clear         -> clear the whole database
        DELETE /clear       -> clear the whole database

    Supported operations:
        post_cell -> requires row, column, and value
        get_cell  -> requires row and column
    """

    def __init__(self, port: int = 1919) -> None:
        self.port = port
        self.base_url = f"http://localhost:{self.port}"
        self.database = InMemoryDatabase()
        self.app = self._create_app()
        self._server: BaseWSGIServer | None = None
        self._server_thread: Thread | None = None

    def start(self) -> None:
        """Start the internal database API server."""
        if self._server_thread and self._server_thread.is_alive():
            raise RuntimeError("Server is already running")

        self._server = make_server("localhost", self.port, self.app)
        self._server_thread = Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()

    def stop(self) -> None:
        """Stop the internal database API server."""
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None

        if self._server_thread:
            self._server_thread.join(timeout=5)
            self._server_thread = None

    def _create_app(self) -> Flask:
        app = Flask(__name__)

        app.add_url_rule("/", view_func=self._health_or_operation, methods=["GET", "POST"])
        app.add_url_rule("/operation", view_func=self._operation, methods=["GET", "POST"])
        app.add_url_rule("/clear", view_func=self._clear, methods=["POST", "DELETE"])

        return app

    def _health_or_operation(self) -> Response | tuple[Response, int] | str:
        action = self._get_argument("action")

        if action is None:
            return "healthy"

        return self._execute_operation(action)

    def _operation(self) -> Response | tuple[Response, int] | str:
        action = self._get_required_argument("action")

        if isinstance(action, tuple):
            return action # Returns an error 400

        return self._execute_operation(action)

    def _execute_operation(self, action: str) -> Response | tuple[Response, int] | str:
        if action == "post_cell":
            return self._post_cell()

        if action == "get_cell":
            return self._get_cell()

        return jsonify({"error": f"Unknown action: {action}"}), 400

    def _post_cell(self) -> tuple[Response, int]:
        row = self._get_required_argument("row")
        column = self._get_required_argument("column")
        value = self._get_required_argument("value")

        if isinstance(row, tuple):
            return row

        if isinstance(column, tuple):
            return column

        if isinstance(value, tuple):
            return value

        self.database.add_cell(row, column, value)

        return jsonify({"message": "Cell saved"}), 200

    def _get_cell(self) -> Any:
        row = self._get_required_argument("row")
        column = self._get_required_argument("column")

        if isinstance(row, tuple):
            return row

        if isinstance(column, tuple):
            return column

        value = self.database.get_cell(row, column)

        if value is None:
            return "Cell not found", 404

        return str(value), 200

    def _clear(self) -> tuple[Response, int]:
        self.database.clear()

        return jsonify({"message": "Database cleared"}), 200

    def _get_argument(self, name: str) -> Any:
        if name in request.args:
            return request.args[name]

        body = request.get_json(silent=True)

        if isinstance(body, dict) and name in body:
            return body[name]

        return None

    def _get_required_argument(self, name: str) -> Any | tuple[Response, int]:
        value = self._get_argument(name)

        if value is None:
            return jsonify({"error": f"Missing required argument: {name}"}), 400

        return value