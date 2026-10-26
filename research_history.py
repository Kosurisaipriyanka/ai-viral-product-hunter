"""Persistent research history using Supabase PostgreSQL or local SQLite."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from database_storage import connect_database, is_postgres

DEFAULT_DB_PATH = Path("research_history.sqlite3")


def _connect(db_path=None):
    # Compatibility helper for existing tests and callers.
    from contextlib import contextmanager
    @contextmanager
    def manager():
        with connect_database(db_path) as connection:
            if is_postgres(db_path):
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS research_runs (
                        id BIGSERIAL PRIMARY KEY,
                        run_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        payload_json TEXT NOT NULL
                    )
                """)
            else:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS research_runs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        run_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        payload_json TEXT NOT NULL
                    )
                """)
            yield connection
    return manager()


def _sql(query: str, db_path=None) -> str:
    return query.replace("?", "%s") if is_postgres(db_path) else query


def save_research_run(run_type: str, title: str, payload: dict[str, Any], db_path: str | Path | None = None) -> int:
    """Save a research result and return its history ID."""
    clean_type, clean_title = str(run_type).strip()[:50], str(title).strip()[:200]
    if not clean_type or not clean_title:
        raise ValueError("run_type and title are required")
    serialized = json.dumps(payload, ensure_ascii=False, default=str)
    with _connect(db_path) as connection:
        cursor = connection.execute(_sql(
            "INSERT INTO research_runs (run_type, title, created_at, payload_json) VALUES (?, ?, ?, ?)",
            db_path), (clean_type, clean_title, datetime.now(timezone.utc).isoformat(), serialized))
        if is_postgres(db_path):
            row = connection.execute("SELECT currval(pg_get_serial_sequence('research_runs', 'id')) AS id").fetchone()
            return int(row["id"])
        return int(cursor.lastrowid)


def list_research_runs(limit: int = 100, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit), 500))
    with _connect(db_path) as connection:
        rows = connection.execute(_sql(
            "SELECT id, run_type, title, created_at, payload_json FROM research_runs ORDER BY id DESC LIMIT ?",
            db_path), (safe_limit,)).fetchall()
    result = []
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
        except (json.JSONDecodeError, TypeError):
            payload = {}
        result.append({"id": row["id"], "run_type": row["run_type"], "title": row["title"],
                       "created_at": row["created_at"], "payload": payload})
    return result


def delete_research_run(run_id: int, db_path: str | Path | None = None) -> bool:
    with _connect(db_path) as connection:
        cursor = connection.execute(_sql("DELETE FROM research_runs WHERE id = ?", db_path), (int(run_id),))
        return cursor.rowcount > 0


def clear_research_history(db_path: str | Path | None = None) -> int:
    with _connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM research_runs")
        return cursor.rowcount
