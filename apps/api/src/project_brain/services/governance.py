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
from project_brain.services.local_chat import (
    extract_corpus,
    latest_transcript_path,
    parse_chat_file,
)


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


def ingest_local_chat(
    *,
    org_id: str,
    repo_id: str,
    path: str | None = None,
    actor: str | None = None,
) -> dict[str, Any]:
    """Explicit: local Cursor/Claude/GPT export → chat_messages + pending decisions."""
    from pathlib import Path

    target = Path(path) if path else latest_transcript_path()
    if target is None or not target.exists():
        return {
            "ok": False,
            "error": "no_transcript",
            "hint": "Pass a .jsonl/.json/.txt path, or set CURSOR_TRANSCRIPTS_DIR",
        }
    turns = parse_chat_file(target)
    if not turns:
        return {"ok": False, "error": "empty_transcript", "path": str(target)}
    session_id = target.stem[:80]
    keep = turns[-40:]
    with get_connection() as conn:
        chat = ChatRepo(conn)
        for turn in keep:
            chat.append(
                org_id=org_id,
                repo_id=repo_id,
                session_id=session_id,
                role=turn["role"] if turn["role"] in {"user", "assistant"} else "user",
                content=turn["content"][:8000],
            )
    corpus = extract_corpus(keep)
    created: list[dict[str, Any]] = []
    for cand in extract_candidates(corpus):
        result = remember_decision(
            org_id=org_id,
            repo_id=repo_id,
            statement=cand["statement"],
            rationale=cand.get("rationale") or f"from {target.name}",
            category=cand.get("category"),
            polarity=cand.get("polarity") or "must",
            actor=actor,
            source="bedrock_extract",
        )
        if result.get("ok"):
            created.append(result)
    return {
        "ok": True,
        "path": str(target),
        "turns": len(keep),
        "created": created,
        "count": len(created),
        "note": "local chat is evidence; confirm in inbox to make law",
    }
