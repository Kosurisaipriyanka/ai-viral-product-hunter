"""Persistent manually collected marketplace evidence using PostgreSQL or SQLite."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from database_storage import connect_database, is_postgres


def _connect(db_path=None):
    from contextlib import contextmanager
    @contextmanager
    def manager():
        with connect_database(db_path) as connection:
            if is_postgres(db_path):
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS marketplace_evidence (
                        id BIGSERIAL PRIMARY KEY, created_at TEXT NOT NULL,
                        product_keyword TEXT NOT NULL, source TEXT NOT NULL,
                        listing_title TEXT NOT NULL, listing_url TEXT NOT NULL,
                        listed_price_inr DOUBLE PRECISION NOT NULL DEFAULT 0,
                        supplier_cost_inr DOUBLE PRECISION NOT NULL DEFAULT 0,
                        shipping_cost_inr DOUBLE PRECISION NOT NULL DEFAULT 0,
                        manually_checked INTEGER NOT NULL DEFAULT 0,
                        evidence_notes TEXT NOT NULL DEFAULT ''
                    )
                """)
            else:
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS marketplace_evidence (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                        product_keyword TEXT NOT NULL, source TEXT NOT NULL,
                        listing_title TEXT NOT NULL, listing_url TEXT NOT NULL,
                        listed_price_inr REAL NOT NULL DEFAULT 0,
                        supplier_cost_inr REAL NOT NULL DEFAULT 0,
                        shipping_cost_inr REAL NOT NULL DEFAULT 0,
                        manually_checked INTEGER NOT NULL DEFAULT 0,
                        evidence_notes TEXT NOT NULL DEFAULT ''
                    )
                """)
            yield connection
    return manager()


def _sql(query: str, db_path=None) -> str:
    return query.replace("?", "%s") if is_postgres(db_path) else query


def save_marketplace_evidence(item: dict[str, Any], db_path: str | Path | None = None) -> int:
    required = ("product_keyword", "source", "listing_title", "listing_url")
    values = {key: str(item.get(key, "")).strip() for key in required}
    if any(not value for value in values.values()):
        raise ValueError("product_keyword, source, listing_title, and listing_url are required")
    if not values["listing_url"].startswith(("https://", "http://")):
        raise ValueError("listing_url must start with http:// or https://")
    params = (datetime.now(timezone.utc).isoformat(), values["product_keyword"], values["source"],
              values["listing_title"], values["listing_url"],
              max(0.0, float(item.get("listed_price_inr") or 0)),
              max(0.0, float(item.get("supplier_cost_inr") or 0)),
              max(0.0, float(item.get("shipping_cost_inr") or 0)),
              int(bool(item.get("manually_checked"))), str(item.get("evidence_notes") or "")[:1000])
    with _connect(db_path) as connection:
        cursor = connection.execute(_sql("""INSERT INTO marketplace_evidence
            (created_at, product_keyword, source, listing_title, listing_url, listed_price_inr,
             supplier_cost_inr, shipping_cost_inr, manually_checked, evidence_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", db_path), params)
        if is_postgres(db_path):
            row = connection.execute("SELECT currval(pg_get_serial_sequence('marketplace_evidence', 'id')) AS id").fetchone()
            return int(row["id"])
        return int(cursor.lastrowid)


def list_marketplace_evidence(limit: int = 500, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit), 1000))
    with _connect(db_path) as connection:
        rows = connection.execute(_sql("SELECT * FROM marketplace_evidence ORDER BY id DESC LIMIT ?", db_path),
                                  (safe_limit,)).fetchall()
    return [dict(row) for row in rows]


def delete_marketplace_evidence(evidence_id: int, db_path: str | Path | None = None) -> bool:
    with _connect(db_path) as connection:
        cursor = connection.execute(_sql("DELETE FROM marketplace_evidence WHERE id = ?", db_path),
                                    (int(evidence_id),))
        return cursor.rowcount > 0
