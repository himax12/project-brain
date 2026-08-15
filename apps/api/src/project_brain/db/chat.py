from __future__ import annotations

from typing import Any

import psycopg

class ChatRepo:
    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn

    def append(
        self,
        *,
        org_id: str,
        repo_id: str,
        session_id: str,
        role: str,
        content: str,
    ) -> dict[str, Any]:
        row = self.conn.execute(
            """
            INSERT INTO chat_messages (org_id, repo_id, session_id, role, content)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (org_id, repo_id, session_id, role, content),
        ).fetchone()
        assert row is not None
        return dict(row)

    def search(
        self,
        org_id: str,
        repo_id: str,
        query: str,
        *,
        session_id: str | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        like = f"%{query}%"
        if session_id:
            rows = self.conn.execute(
                """
                SELECT * FROM chat_messages
                WHERE org_id = %s AND repo_id = %s AND session_id = %s
                  AND content ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (org_id, repo_id, session_id, like, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT * FROM chat_messages
                WHERE org_id = %s AND repo_id = %s AND content ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (org_id, repo_id, like, limit),
            ).fetchall()
        return [dict(r) for r in rows]


def public_chat(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["id"] = str(out["id"])
    if out.get("created_at") is not None:
        out["created_at"] = out["created_at"].isoformat()
    return out
