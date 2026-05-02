from urllib.parse import quote

import requests


class DatabaseApiError(Exception):
    pass


class DatabaseValueNotFoundError(DatabaseApiError):
    pass


class DatabaseApiClient:
    def __init__(self, base_url: str, timeout: float = 3.0):
        self.base_url = normalize_base_url(base_url)
        self.timeout = timeout

    def create_cell(self, table: str, row: str, cell: str, value: str) -> None:
        self._request(
            "POST",
            cell_path(table, row, cell),
            json_body={"value": value},
        )

    def read_cell(self, table: str, row: str, cell: str) -> str:
        response = self._request("GET", cell_path(table, row, cell))

        return str(response.get("value", ""))

    def update_cell(self, table: str, row: str, cell: str, value: str) -> None:
        self._request(
            "PUT",
            cell_path(table, row, cell),
            json_body={"value": value},
        )

    def delete_cell(self, table: str, row: str, cell: str) -> None:
        self._request("DELETE", cell_path(table, row, cell))

    def create_row(self, table: str, row: str, values: dict[str, str]) -> None:
        self._request("POST", row_path(table, row), json_body=values)

    def read_row(self, table: str, row: str) -> dict[str, str]:
        response = self._request("GET", row_path(table, row))

        return normalize_row(response.get("row", {}))

    def update_row(self, table: str, row: str, values: dict[str, str]) -> None:
        self._request("PUT", row_path(table, row), json_body=values)

    def delete_row(self, table: str, row: str) -> None:
        self._request("DELETE", row_path(table, row))

    def list_rows(self, table: str) -> list[dict[str, str]]:
        response = self._request("GET", rows_path(table))

        return [normalize_row(row) for row in response.get("rows", [])]

    def clear_database(self) -> None:
        self._request("DELETE", "/database")

    def _request(
        self,
        method: str,
        path: str,
        json_body: dict[str, str] | None = None,
    ) -> dict:
        response = send_request(method, self.url_for(path), json_body, self.timeout)
        if response.status_code == 404:
            raise DatabaseValueNotFoundError("Not found")

        if not 200 <= response.status_code < 300:
            raise DatabaseApiError(error_message_from(response))

        return json_from(response)

    def url_for(self, path: str) -> str:
        return f"{self.base_url}{path}"


def send_request(method: str, url: str, json_body: dict | None, timeout: float):
    try:
        return requests.request(method, url, json=json_body, timeout=timeout)
    except requests.RequestException as error:
        raise DatabaseApiError(str(error)) from error


def normalize_base_url(base_url: str) -> str:
    normalized_url = base_url.strip().rstrip("/")
    if not normalized_url:
        raise DatabaseApiError("Database API base URL is required.")

    return normalized_url


def cell_path(table: str, row: str, cell: str) -> str:
    return f"{row_path(table, row)}/cells/{path_segment(cell)}"


def row_path(table: str, row: str) -> str:
    return f"{rows_path(table)}/{path_segment(row)}"


def rows_path(table: str) -> str:
    return f"/tables/{path_segment(table)}/rows"


def path_segment(value: str) -> str:
    return quote(str(value), safe="")


def normalize_row(row: dict) -> dict[str, str]:
    return {key: str(value) for key, value in row.items()}


def error_message_from(response) -> str:
    body = json_from(response)
    if "error" in body:
        return str(body["error"])

    return f"Database API request failed with status {response.status_code}."


def json_from(response) -> dict:
    try:
        body = response.json()
    except ValueError:
        return {}

    if isinstance(body, dict):
        return body

    return {}
