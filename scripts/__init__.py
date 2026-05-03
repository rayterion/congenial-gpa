"""Development database helper used by behave tests."""
import os
import sqlite3
import tempfile


class DevDatabase:
    def __init__(self) -> None:
        self._db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._db_file.close()
        self._db_path = self._db_file.name

    def run(self) -> None:
        """Initialise the SQLite database file."""
        conn = sqlite3.connect(self._db_path)
        conn.close()

    def get_db_url(self) -> str:
        return f"sqlite:///{self._db_path}"

    def shutdown(self) -> None:
        """Remove the temporary database file."""
        try:
            os.unlink(self._db_path)
        except FileNotFoundError:
            pass
