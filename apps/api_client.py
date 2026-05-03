"""HTTP client for the Database API."""
import requests
from typing import Optional


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def set_cell(self, table: str, row_id: str, cell: str, value: str) -> dict:
        return self._post(f"/{table}/{row_id}", {cell: value})

    def get_cell(self, table: str, row_id: str, cell: str) -> Optional[dict]:
        return self._get(f"/{table}/{row_id}/{cell}")

    def update_cell(self, table: str, row_id: str, cell: str, value: str) -> dict:
        return self._put(f"/{table}/{row_id}", {cell: value})

    def delete_cell(self, table: str, row_id: str, cell: str) -> dict:
        return self._delete(f"/{table}/{row_id}/{cell}")

    def add_row(self, table: str, row_id: str, data: dict) -> dict:
        return self._post(f"/{table}/{row_id}", data)

    def get_row(self, table: str, row_id: str) -> Optional[dict]:
        return self._get(f"/{table}/{row_id}")

    def update_row(self, table: str, row_id: str, data: dict) -> dict:
        return self._put(f"/{table}/{row_id}", data)

    def delete_row(self, table: str, row_id: str) -> dict:
        return self._delete(f"/{table}/{row_id}")

    def list_rows(self, table: str) -> dict:
        return self._get(f"/{table}") or {}

    def clear_database(self) -> dict:
        return self._delete("/clear")

    def _get(self, path: str) -> Optional[dict]:
        response = requests.get(self._base_url + path)
        if response.status_code == 404:
            return None
        return response.json()

    def _post(self, path: str, body: dict) -> dict:
        response = requests.post(self._base_url + path, json=body)
        return response.json()

    def _put(self, path: str, body: dict) -> dict:
        response = requests.put(self._base_url + path, json=body)
        return response.json()

    def _delete(self, path: str) -> dict:
        response = requests.delete(self._base_url + path)
        return response.json()
