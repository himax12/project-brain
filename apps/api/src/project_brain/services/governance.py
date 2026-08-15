from __future__ import annotations

from typing import Any
from uuid import UUID

from project_brain.db.chat import ChatRepo
from project_brain.db.memories import MemoryRepo
from project_brain.db.pool import get_connection
from project_brain.serialize import public_memory
from project_brain.services.conflicts import find_conflicts
from project_brain.services.deny_list import deny_reason
from project_brain.services.embeddings import embed_text
from project_brain.services.extract import extract_candidates


def remember_decision(
    *,
    org_id: str,
    repo_id: str,
    statement: str,
    rationale: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    polarity: str = "must",
    actor: str | None = None,
    source: str = "user",
) -> dict[str, Any]:
    denied = deny_reason(statement)
    if denied:
        return {"ok": False, "denied": denied}
    with get_connection() as conn:
        repo = MemoryRepo(conn)
        conflicts = find_conflicts(statement, repo.list_active(org_id, repo_id))
        provenance = {"conflicts": conflicts} if conflicts else None
        row = repo.insert_pending(
            org_id=org_id,
            repo_id=repo_id,
            statement=statement,
            rationale=rationale,
            category=category,
            tags=tags,
            polarity=polarity,
            actor=actor,
            source=source,
            provenance=provenance,
        )
    return {
        "ok": True,
        "status": "pending_review",
        "conflicts": conflicts,
        **public_memory(row),
    }


def confirm_and_embed(
    memory_id: UUID,
    org_id: str,
    repo_id: str,
    *,
    actor: str | None = None,
) -> dict[str, Any]:
    with get_connection() as conn:
        repo = MemoryRepo(conn)
        row = repo.confirm(memory_id, org_id, repo_id, actor=actor)
        try:
            repo.set_embedding(row["id"], embed_text(str(row["statement"])))
            row = repo.get(memory_id, org_id, repo_id) or row
        except Exception:
            # VECTOR write optional; active status still stands.
            pass
    return public_memory(row)


def ingest_session(
    *,
    org_id: str,
    repo_id: str,
    transcript: str,
    session_id: str = "explicit",
    actor: str | None = None,
) -> dict[str, Any]:
    with get_connection() as conn:
        chat = ChatRepo(conn)
        chat.append(
            org_id=org_id,
            repo_id=repo_id,
            session_id=session_id,
            role="user",
            content=transcript,
        )
    created: list[dict[str, Any]] = []
    skipped_conflicts = 0
    for cand in extract_candidates(transcript):
        result = remember_decision(
            org_id=org_id,
            repo_id=repo_id,
            statement=cand["statement"],
            rationale=cand.get("rationale"),
            category=cand.get("category"),
            polarity=cand.get("polarity") or "must",
            actor=actor,
            source="bedrock_extract",
        )
        if result.get("ok"):
            created.append(result)
            if result.get("conflicts"):
                skipped_conflicts += 1
    return {
        "ok": True,
        "created": created,
        "count": len(created),
        "conflicted": skipped_conflicts,
        "note": "candidates stay pending_review until confirm (Lean E)",
    }
