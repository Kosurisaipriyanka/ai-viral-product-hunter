"""Local SQLite persistence for manually collected marketplace evidence."""
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
    connection.execute("""
        CREATE TABLE IF NOT EXISTS marketplace_evidence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            product_keyword TEXT NOT NULL,
            source TEXT NOT NULL,
            listing_title TEXT NOT NULL,
            listing_url TEXT NOT NULL,
            listed_price_inr REAL NOT NULL DEFAULT 0,
            supplier_cost_inr REAL NOT NULL DEFAULT 0,
            shipping_cost_inr REAL NOT NULL DEFAULT 0,
            manually_checked INTEGER NOT NULL DEFAULT 0,
            evidence_notes TEXT NOT NULL DEFAULT ''
        )
    """)
    return connection


def save_marketplace_evidence(item: dict[str, Any], db_path: str | Path | None = None) -> int:
    """Save one manually entered listing and return its ID."""
    required = ("product_keyword", "source", "listing_title", "listing_url")
    values = {key: str(item.get(key, "")).strip() for key in required}
    if any(not value for value in values.values()):
        raise ValueError("product_keyword, source, listing_title, and listing_url are required")
    if not values["listing_url"].startswith(("https://", "http://")):
        raise ValueError("listing_url must start with http:// or https://")
    with _connect(db_path) as connection:
        cursor = connection.execute(
            """INSERT INTO marketplace_evidence
            (created_at, product_keyword, source, listing_title, listing_url,
             listed_price_inr, supplier_cost_inr, shipping_cost_inr, manually_checked, evidence_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(), values["product_keyword"], values["source"],
                values["listing_title"], values["listing_url"],
                max(0.0, float(item.get("listed_price_inr") or 0)),
                max(0.0, float(item.get("supplier_cost_inr") or 0)),
                max(0.0, float(item.get("shipping_cost_inr") or 0)),
                int(bool(item.get("manually_checked"))), str(item.get("evidence_notes") or "")[:1000],
            ),
        )
        return int(cursor.lastrowid)


def list_marketplace_evidence(limit: int = 500, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    """Return newest evidence entries first."""
    safe_limit = max(1, min(int(limit), 1000))
    with _connect(db_path) as connection:
        rows = connection.execute(
            "SELECT * FROM marketplace_evidence ORDER BY id DESC LIMIT ?", (safe_limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def delete_marketplace_evidence(evidence_id: int, db_path: str | Path | None = None) -> bool:
    """Delete one evidence entry by ID."""
    with _connect(db_path) as connection:
        cursor = connection.execute("DELETE FROM marketplace_evidence WHERE id = ?", (int(evidence_id),))
        return cursor.rowcount > 0
