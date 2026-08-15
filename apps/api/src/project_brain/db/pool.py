from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from project_brain.config import get_settings


def connect() -> psycopg.Connection:
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is empty. Copy .env.example to .env and set the CockroachDB URL."
        )
    return psycopg.connect(settings.database_url, row_factory=dict_row)


@contextmanager
def get_connection() -> Iterator[psycopg.Connection]:
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
