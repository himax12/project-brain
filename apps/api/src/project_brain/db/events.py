from __future__ import annotations

from typing import Any
from uuid import UUID

import psycopg


def append_event(
    conn: psycopg.Connection,
    *,
    org_id: str,
    repo_id: str,
    event_type: str,
    memory_id: UUID | None = None,
    actor: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO memory_events (memory_id, org_id, repo_id, event_type, actor, payload)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb)
        """,
        (memory_id, org_id, repo_id, event_type, actor, _json(payload)),
    )


def _json(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    import json

    return json.dumps(payload)
