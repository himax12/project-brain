from __future__ import annotations

from uuid import UUID

from mcp.server.mcpserver import MCPServer

from project_brain.config import get_settings
from project_brain.db.chat import ChatRepo, public_chat
from project_brain.db.memories import MemoryRepo
from project_brain.db.pool import get_connection
from project_brain.graphs.memory_recall import recall
from project_brain.graphs.session_boot import get_context
from project_brain.serialize import public_memory
from project_brain.services.deny_list import deny_reason
from project_brain.services.embeddings import embed_text
from project_brain.services.governance import (
    confirm_and_embed,
    ingest_local_chat,
    ingest_session,
    remember_decision,
)

mcp = MCPServer("project-brain")


def _scope(org_id: str | None, repo_id: str | None) -> tuple[str, str]:
    s = get_settings()
    return org_id or s.default_org_id, repo_id or s.default_repo_id


@mcp.tool()
def remember(
    statement: str,
    org_id: str | None = None,
    repo_id: str | None = None,
    rationale: str | None = None,
    category: str | None = None,
    polarity: str = "must",
    actor: str | None = None,
) -> dict:
    """Save a lasting project decision as pending_review (not yet law)."""
    org_id, repo_id = _scope(org_id, repo_id)
    return remember_decision(
        org_id=org_id,
        repo_id=repo_id,
        statement=statement,
        rationale=rationale,
        category=category,
        polarity=polarity,
        actor=actor,
    )


@mcp.tool()
def list_pending(org_id: str | None = None, repo_id: str | None = None, limit: int = 50) -> dict:
    """List memories waiting for human confirm."""
    org_id, repo_id = _scope(org_id, repo_id)
    with get_connection() as conn:
        items = MemoryRepo(conn).list_pending(org_id, repo_id, limit=limit)
    return {"items": [public_memory(i) for i in items]}


@mcp.tool(name="get_context")
def get_context_tool(
    org_id: str | None = None,
    repo_id: str | None = None,
    limit: int = 12,
) -> dict:
    """Boot packet: active-only project context. Call at session start. must_not pins first."""
    org_id, repo_id = _scope(org_id, repo_id)
    return get_context(org_id, repo_id, limit=limit)


@mcp.tool(name="recall")
def recall_memory(
    query: str,
    org_id: str | None = None,
    repo_id: str | None = None,
    intent_hint: str | None = None,
) -> dict:
    """Mid-task authority packet (pin/decide/do_not_use), not a flat score list."""
    org_id, repo_id = _scope(org_id, repo_id)
    return recall(org_id, repo_id, query, intent_hint=intent_hint)


@mcp.tool(name="ingest_session")
def ingest_session_tool(
    transcript: str,
    session_id: str = "explicit",
    org_id: str | None = None,
    repo_id: str | None = None,
    actor: str | None = None,
) -> dict:
    """Explicit extract only (Lean E). Candidates stay pending_review."""
    org_id, repo_id = _scope(org_id, repo_id)
    return ingest_session(
        org_id=org_id,
        repo_id=repo_id,
        transcript=transcript,
        session_id=session_id,
        actor=actor,
    )


@mcp.tool(name="ingest_local_chat")
def ingest_local_chat_tool(
    path: str | None = None,
    org_id: str | None = None,
    repo_id: str | None = None,
    actor: str | None = None,
) -> dict:
    """Pull Cursor/Claude/GPT local chat export into pending memories. Does not auto-activate."""
    org_id, repo_id = _scope(org_id, repo_id)
    return ingest_local_chat(org_id=org_id, repo_id=repo_id, path=path, actor=actor)


@mcp.tool()
def search_chat(
    query: str,
    org_id: str | None = None,
    repo_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    """Chat evidence only — never must_obey."""
    org_id, repo_id = _scope(org_id, repo_id)
    with get_connection() as conn:
        items = ChatRepo(conn).search(org_id, repo_id, query, session_id=session_id)
    return {"items": [public_chat(i) for i in items], "authority": "evidence"}


@mcp.tool()
def resolve_conflict(
    pending_id: str,
    existing_id: str,
    choice: str,
    org_id: str | None = None,
    repo_id: str | None = None,
    actor: str | None = None,
) -> dict:
    """keep_existing rejects the pending row; switch_to_pending supersedes the active one."""
    org_id, repo_id = _scope(org_id, repo_id)
    try:
        with get_connection() as conn:
            repo = MemoryRepo(conn)
            if choice == "keep_existing":
                row = repo.reject(UUID(pending_id), org_id, repo_id, actor=actor)
                return {"ok": True, "rejected": public_memory(row)}
            if choice != "switch_to_pending":
                return {"ok": False, "error": "choice must be keep_existing or switch_to_pending"}
            result = repo.resolve_switch(
                UUID(pending_id), UUID(existing_id), org_id, repo_id, actor=actor
            )
            try:
                repo.set_embedding(result["new"]["id"], embed_text(str(result["new"]["statement"])))
            except Exception:
                pass
            return {"ok": True, "old": public_memory(result["old"]), "new": public_memory(result["new"])}
    except ValueError as e:
        return {"ok": False, "error": str(e)}


@mcp.tool()
def confirm_memory(
    pending_id: str,
    org_id: str | None = None,
    repo_id: str | None = None,
    actor: str | None = None,
) -> dict:
    """Promote pending_review → active (project law) and write embedding."""
    org_id, repo_id = _scope(org_id, repo_id)
    try:
        row = confirm_and_embed(UUID(pending_id), org_id, repo_id, actor=actor)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, **row}


@mcp.tool()
def reject_memory(
    pending_id: str,
    org_id: str | None = None,
    repo_id: str | None = None,
    actor: str | None = None,
) -> dict:
    """Drop a pending candidate."""
    org_id, repo_id = _scope(org_id, repo_id)
    try:
        with get_connection() as conn:
            row = MemoryRepo(conn).reject(UUID(pending_id), org_id, repo_id, actor=actor)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, **public_memory(row)}


@mcp.tool()
def get_memory(
    memory_id: str,
    org_id: str | None = None,
    repo_id: str | None = None,
) -> dict:
    """Full memory row by id (any status, labeled)."""
    org_id, repo_id = _scope(org_id, repo_id)
    with get_connection() as conn:
        row = MemoryRepo(conn).get(UUID(memory_id), org_id, repo_id)
    if not row:
        return {"ok": False, "error": "not found"}
    return {"ok": True, **public_memory(row)}


@mcp.tool()
def supersede_memory(
    old_id: str,
    statement: str,
    org_id: str | None = None,
    repo_id: str | None = None,
    rationale: str | None = None,
    polarity: str = "must",
    actor: str | None = None,
) -> dict:
    """Replace an active decision. Old row becomes superseded with invalid_at set."""
    org_id, repo_id = _scope(org_id, repo_id)
    reason = deny_reason(statement)
    if reason:
        return {"ok": False, "denied": reason}
    try:
        with get_connection() as conn:
            result = MemoryRepo(conn).supersede(
                UUID(old_id),
                org_id,
                repo_id,
                statement=statement,
                rationale=rationale,
                polarity=polarity,
                actor=actor,
            )
            try:
                MemoryRepo(conn).set_embedding(result["new"]["id"], embed_text(statement))
            except Exception:
                pass
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    return {
        "ok": True,
        "old": public_memory(result["old"]),
        "new": public_memory(result["new"]),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
