"""Local SQLite storage for research runs.

History is stored on this computer only; no credentials or API keys are saved.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(os.getenv("PRODUCT_HUNTER_HISTORY_DB", "research_history.sqlite3"))


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS research_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_type TEXT NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            payload_json TEXT NOT NULL
        )
        """
    )
    return connection


def save_research_run(
    run_type: str,
    title: str,
    payload: dict[str, Any],
    db_path: str | Path | None = None,
) -> int:
    """Save a research result locally and return its history ID."""
    clean_type = str(run_type).strip()[:50]
    clean_title = str(title).strip()[:200]
    if not clean_type or not clean_title:
        raise ValueError("run_type and title are required")
    serialized = json.dumps(payload, ensure_ascii=False, default=str)
    with _connect(db_path) as connection:
        cursor = connection.execute(
            "INSERT INTO research_runs (run_type, title, created_at, payload_json) VALUES (?, ?, ?, ?)",
            (clean_type, clean_title, datetime.now(timezone.utc).isoformat(), serialized),
        )
        return int(cursor.lastrowid)


def list_research_runs(
    limit: int = 100,
    db_path: str | Path | None = None,
) -> list[dict[str, Any]]:
    """Return newest saved runs first, with payloads decoded from JSON."""
    safe_limit = max(1, min(int(limit), 500))
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT id, run_type, title, created_at, payload_json FROM research_runs ORDER BY id DESC LIMIT ?",
            (safe_limit,),
        ).fetchall()
    result = []
    for row in rows:
        try:
            payload = json.loads(row["payload_json"])
        except (json.JSONDecodeError, TypeError):
            payload = {}
        result.append({
            "id": row["id"],
            "run_type": row["run_type"],
            "title": row["title"],
            "created_at": row["created_at"],
            "payload": payload,
        })
    return result


def delete_research_run(run_id: int, db_path: str | Path | None = None) -> bool:
    """Delete one locally saved run; return whether a row was deleted."""
    with _connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM research_runs WHERE id = ?", (int(run_id),))
        return cursor.rowcount > 0


def clear_research_history(db_path: str | Path | None = None) -> int:
    """Delete all saved runs and return the number removed."""
    with _connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM research_runs")
        return cursor.rowcount
