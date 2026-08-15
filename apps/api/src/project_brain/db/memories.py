from __future__ import annotations

from typing import Any
from uuid import UUID

import psycopg

from project_brain.db.events import append_event


class MemoryRepo:
    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn

    def insert_pending(
        self,
        *,
        org_id: str,
        repo_id: str,
        statement: str,
        rationale: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        polarity: str = "must",
        importance: float = 0.5,
        confidence: float = 0.8,
        source: str = "user",
        actor: str | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = self.conn.execute(
            """
            INSERT INTO memories (
              org_id, repo_id, statement, rationale, category, tags,
              polarity, status, importance, confidence, source, provenance
            )
            VALUES (
              %s, %s, %s, %s, %s, %s,
              %s, 'pending_review', %s, %s, %s, %s::jsonb
            )
            RETURNING *
            """,
            (
                org_id,
                repo_id,
                statement,
                rationale,
                category,
                tags or [],
                polarity,
                importance,
                confidence,
                source,
                _json(provenance),
            ),
        ).fetchone()
        assert row is not None
        append_event(
            self.conn,
            org_id=org_id,
            repo_id=repo_id,
            event_type="created",
            memory_id=row["id"],
            actor=actor,
            payload={"status": "pending_review"},
        )
        return dict(row)

    def list_pending(self, org_id: str, repo_id: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            """
            SELECT id, statement, rationale, category, tags, polarity, source,
                   confidence, created_at, provenance
            FROM memories
            WHERE org_id = %s AND repo_id = %s AND status = 'pending_review'
            ORDER BY created_at ASC
            LIMIT %s
            """,
            (org_id, repo_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get(self, memory_id: UUID, org_id: str, repo_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            """
            SELECT * FROM memories
            WHERE id = %s AND org_id = %s AND repo_id = %s
            """,
            (memory_id, org_id, repo_id),
        ).fetchone()
        return dict(row) if row else None

    def confirm(
        self,
        memory_id: UUID,
        org_id: str,
        repo_id: str,
        *,
        actor: str | None = None,
    ) -> dict[str, Any]:
        row = self.conn.execute(
            """
            UPDATE memories
            SET status = 'active', updated_at = now()
            WHERE id = %s AND org_id = %s AND repo_id = %s AND status = 'pending_review'
            RETURNING *
            """,
            (memory_id, org_id, repo_id),
        ).fetchone()
        if row is None:
            raise ValueError("confirm_failed: not pending or wrong scope")
        append_event(
            self.conn,
            org_id=org_id,
            repo_id=repo_id,
            event_type="confirmed",
            memory_id=memory_id,
            actor=actor,
        )
        return dict(row)

    def reject(
        self,
        memory_id: UUID,
        org_id: str,
        repo_id: str,
        *,
        actor: str | None = None,
    ) -> dict[str, Any]:
        row = self.conn.execute(
            """
            UPDATE memories
            SET status = 'rejected', updated_at = now()
            WHERE id = %s AND org_id = %s AND repo_id = %s AND status = 'pending_review'
            RETURNING *
            """,
            (memory_id, org_id, repo_id),
        ).fetchone()
        if row is None:
            raise ValueError("reject_failed: not pending or wrong scope")
        append_event(
            self.conn,
            org_id=org_id,
            repo_id=repo_id,
            event_type="rejected",
            memory_id=memory_id,
            actor=actor,
        )
        return dict(row)

    def boot_active(
        self,
        org_id: str,
        repo_id: str,
        *,
        limit: int = 12,
        categories: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        if categories:
            rows = self.conn.execute(
                """
                SELECT id, statement, rationale, category, tags, polarity, importance, updated_at
                FROM memories
                WHERE org_id = %s AND repo_id = %s AND status = 'active'
                  AND category = ANY(%s)
                ORDER BY (polarity = 'must_not') DESC, importance DESC, updated_at DESC
                LIMIT %s
                """,
                (org_id, repo_id, categories, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """
                SELECT id, statement, rationale, category, tags, polarity, importance, updated_at
                FROM memories
                WHERE org_id = %s AND repo_id = %s AND status = 'active'
                ORDER BY (polarity = 'must_not') DESC, importance DESC, updated_at DESC
                LIMIT %s
                """,
                (org_id, repo_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def supersede(
        self,
        old_id: UUID,
        org_id: str,
        repo_id: str,
        *,
        statement: str,
        rationale: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        polarity: str = "must",
        actor: str | None = None,
    ) -> dict[str, Any]:
        old = self.conn.execute(
            """
            UPDATE memories
            SET status = 'superseded', invalid_at = now(), updated_at = now()
            WHERE id = %s AND org_id = %s AND repo_id = %s AND status = 'active'
            RETURNING *
            """,
            (old_id, org_id, repo_id),
        ).fetchone()
        if old is None:
            raise ValueError("supersede_failed: old row not active or wrong scope")
        new = self.conn.execute(
            """
            INSERT INTO memories (
              org_id, repo_id, statement, rationale, category, tags,
              polarity, status, importance, confidence, source, supersedes_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', 0.7, 0.9, 'user', %s)
            RETURNING *
            """,
            (
                org_id,
                repo_id,
                statement,
                rationale,
                category or old.get("category"),
                tags if tags is not None else old.get("tags"),
                polarity,
                old_id,
            ),
        ).fetchone()
        assert new is not None
        append_event(
            self.conn,
            org_id=org_id,
            repo_id=repo_id,
            event_type="superseded",
            memory_id=old_id,
            actor=actor,
            payload={"replacement_id": str(new["id"])},
        )
        append_event(
            self.conn,
            org_id=org_id,
            repo_id=repo_id,
            event_type="confirmed",
            memory_id=new["id"],
            actor=actor,
            payload={"via": "supersede", "supersedes_id": str(old_id)},
        )
        return {"old": dict(old), "new": dict(new)}


def _json(payload: dict[str, Any] | None) -> str | None:
    if payload is None:
        return None
    import json

    return json.dumps(payload)
