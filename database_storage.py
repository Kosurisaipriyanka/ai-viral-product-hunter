"""Database connection helpers for hosted PostgreSQL and local SQLite."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Any

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


@contextmanager
def connect_database(db_path: str | Path | None = None) -> Iterator[Any]:
    """Use SQLite for explicit local/test paths; otherwise use Supabase if configured."""
    if db_path is not None or not DATABASE_URL:
        path = Path(db_path) if db_path is not None else Path(
            os.getenv("PRODUCT_HUNTER_HISTORY_DB", "research_history.sqlite3")
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(str(path))
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return

    import psycopg
    from psycopg.rows import dict_row

    connection = psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=10)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def is_postgres(db_path: str | Path | None = None) -> bool:
    return db_path is None and bool(DATABASE_URL)
