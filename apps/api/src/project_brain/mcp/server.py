from __future__ import annotations

from uuid import UUID

from mcp.server.mcpserver import MCPServer

from project_brain.config import get_settings
from project_brain.db.memories import MemoryRepo
from project_brain.db.pool import get_connection
from project_brain.graphs.session_boot import get_context
from project_brain.services.deny_list import deny_reason

mcp = MCPServer("project-brain")


def _scope(org_id: str | None, repo_id: str | None) -> tuple[str, str]:
    s = get_settings()
    return org_id or s.default_org_id, repo_id or s.default_repo_id


def _public(row: dict) -> dict:
    out = dict(row)
    out["id"] = str(out["id"])
    if out.get("supersedes_id"):
        out["supersedes_id"] = str(out["supersedes_id"])
    out.pop("embedding", None)
    for key in ("created_at", "updated_at", "invalid_at"):
        if out.get(key) is not None:
            out[key] = out[key].isoformat()
    return out


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
    reason = deny_reason(statement)
    if reason:
        return {"ok": False, "denied": reason}
    org_id, repo_id = _scope(org_id, repo_id)
    with get_connection() as conn:
        row = MemoryRepo(conn).insert_pending(
            org_id=org_id,
            repo_id=repo_id,
            statement=statement,
            rationale=rationale,
            category=category,
            polarity=polarity,
            actor=actor,
        )
    return {"ok": True, "status": "pending_review", **_public(row)}


@mcp.tool()
def list_pending(org_id: str | None = None, repo_id: str | None = None, limit: int = 50) -> dict:
    """List memories waiting for human confirm."""
    org_id, repo_id = _scope(org_id, repo_id)
    with get_connection() as conn:
        items = MemoryRepo(conn).list_pending(org_id, repo_id, limit=limit)
    return {"items": [_public(i) for i in items]}


@mcp.tool(name="get_context")
def get_context_tool(
    org_id: str | None = None,
    repo_id: str | None = None,
    limit: int = 12,
) -> dict:
    """Boot packet: active-only project context. Call at session start. must_not pins first."""
    org_id, repo_id = _scope(org_id, repo_id)
    return get_context(org_id, repo_id, limit=limit)


@mcp.tool()
def confirm_memory(
    pending_id: str,
    org_id: str | None = None,
    repo_id: str | None = None,
    actor: str | None = None,
) -> dict:
    """Promote pending_review → active (project law)."""
    org_id, repo_id = _scope(org_id, repo_id)
    try:
        with get_connection() as conn:
            row = MemoryRepo(conn).confirm(UUID(pending_id), org_id, repo_id, actor=actor)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    return {"ok": True, **_public(row)}


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
    return {"ok": True, **_public(row)}


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
    return {"ok": True, **_public(row)}


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
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    return {
        "ok": True,
        "old": _public(result["old"]),
        "new": _public(result["new"]),
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
