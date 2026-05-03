"""
Dynamic Database API using SQLModel + PostgreSQL, served via Flask.

Physical layout per logical table named <table_name>:
    <table_name>_rows    – row_name  → id
    <table_name>_columns – col_name  → id
    <table_name>_cells   – (row_id, col_id, value)

Rows and columns are created on-demand.

Usage:
    db = DatabaseAPI("postgresql://postgres:postgres@localhost:5432/mydb", port=4040)
    db.run()   # blocks; or call db.start() to run in a background thread
"""

from __future__ import annotations

import threading
from typing import Any, Optional

from sqlalchemy import text
from sqlmodel import Field, Session, SQLModel, create_engine, select
from flask import Flask, request, jsonify


# ---------------------------------------------------------------------------
# Dynamic model factory
# ---------------------------------------------------------------------------

_MODEL_CACHE: dict[str, tuple] = {}


def _make_models(table_name: str):
    if table_name in _MODEL_CACHE:
        return _MODEL_CACHE[table_name]

    rows_table  = f"{table_name}_rows"
    cols_table  = f"{table_name}_columns"
    cells_table = f"{table_name}_cells"

    class RowDef(SQLModel, table=True):
        __tablename__  = rows_table
        __table_args__ = {"extend_existing": True}
        id:   Optional[int] = Field(default=None, primary_key=True)
        name: str           = Field(index=True, unique=True)

    class ColDef(SQLModel, table=True):
        __tablename__  = cols_table
        __table_args__ = {"extend_existing": True}
        id:   Optional[int] = Field(default=None, primary_key=True)
        name: str           = Field(index=True, unique=True)

    class Cell(SQLModel, table=True):
        __tablename__  = cells_table
        __table_args__ = {"extend_existing": True}
        id:     Optional[int] = Field(default=None, primary_key=True)
        row_id: int           = Field(foreign_key=f"{rows_table}.id", index=True)
        col_id: int           = Field(foreign_key=f"{cols_table}.id", index=True)
        value:  Optional[str] = None

    _MODEL_CACHE[table_name] = (RowDef, ColDef, Cell)
    return RowDef, ColDef, Cell


# ---------------------------------------------------------------------------
# DatabaseAPI
# ---------------------------------------------------------------------------

class DatabaseAPI:
    def __init__(self, database_url: str, port: int = 4040, *, echo: bool = False) -> None:
        self.engine   = create_engine(database_url, echo=echo)
        self.port     = port
        self.base_url = f"http://localhost:{port}"
        self.app      = self._build_app()

    # ------------------------------------------------------------------
    # Flask app
    # ------------------------------------------------------------------

    def _build_app(self) -> Flask:
        app = Flask(__name__)

        @app.post("/<table_name>/<row_name>/<col_name>")
        def post_cell(table_name: str, row_name: str, col_name: str):
            body = request.get_json(silent=True) or {}
            value = body.get("data")
            if value is None:
                return jsonify({"error": "Missing 'data' field"}), 400

            self.set_cell(table_name, row_name, col_name, value)
            return jsonify({"status": "ok"}), 200
        @app.get("/")
        def health_check():
            return "API is healthy", 200
        return app

    # ------------------------------------------------------------------
    # Server lifecycle
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start Flask in the current thread (blocks)."""
        self.app.run(port=self.port)

    def start(self) -> None:
        """Start Flask in a background daemon thread (non-blocking)."""
        t = threading.Thread(target=lambda: self.app.run(port=self.port), daemon=True)
        t.start()

    # ------------------------------------------------------------------
    # Cell logic
    # ------------------------------------------------------------------

    def set_cell(self, table_name: str, row_name: str, col_name: str, value: Any) -> None:
        """Write value to (row_name, col_name); create table/row/col if needed."""
        RowDef, ColDef, Cell = _make_models(table_name)
        self._ensure_tables(RowDef, ColDef, Cell)

        with Session(self.engine) as session:
            row  = self._upsert_name(session, RowDef, row_name)
            col  = self._upsert_name(session, ColDef, col_name)
            cell = session.exec(
                select(Cell).where(Cell.row_id == row.id, Cell.col_id == col.id)
            ).first()

            if cell is None:
                session.add(Cell(row_id=row.id, col_id=col.id, value=str(value)))
            else:
                cell.value = str(value)
                session.add(cell)

            session.commit()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _ensure_tables(self, RowDef, ColDef, Cell) -> None:
        SQLModel.metadata.create_all(
            self.engine,
            tables=[RowDef.__table__, ColDef.__table__, Cell.__table__],
        )

    @staticmethod
    def _upsert_name(session: Session, Model, name: str):
        instance = session.exec(select(Model).where(Model.name == name)).first()
        if instance is None:
            instance = Model(name=name)
            session.add(instance)
            session.commit()
            session.refresh(instance)
        return instance


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/mydb"
    db = DatabaseAPI(DATABASE_URL, port=4040)
    db.run()