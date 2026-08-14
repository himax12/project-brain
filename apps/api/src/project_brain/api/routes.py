from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from project_brain.api.deps import require_api_key
from project_brain.config import get_settings
from project_brain.db.memories import MemoryRepo
from project_brain.db.pool import get_connection
from project_brain.graphs.session_boot import get_context
from project_brain.services.deny_list import deny_reason

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])


class RememberBody(BaseModel):
    statement: str
    org_id: str | None = None
    repo_id: str | None = None
    rationale: str | None = None
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    polarity: str = "must"
    actor: str | None = None


class SupersedeBody(BaseModel):
    statement: str
    rationale: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    polarity: str = "must"
    actor: str | None = None


def _scope(org_id: str | None, repo_id: str | None) -> tuple[str, str]:
    s = get_settings()
    return org_id or s.default_org_id, repo_id or s.default_repo_id


@router.post("/remember")
def remember(body: RememberBody) -> dict:
    reason = deny_reason(body.statement)
    if reason:
        raise HTTPException(status_code=400, detail={"denied": reason})
    org_id, repo_id = _scope(body.org_id, body.repo_id)
    with get_connection() as conn:
        row = MemoryRepo(conn).insert_pending(
            org_id=org_id,
            repo_id=repo_id,
            statement=body.statement,
            rationale=body.rationale,
            category=body.category,
            tags=body.tags,
            polarity=body.polarity,
            actor=body.actor,
        )
    return _public(row)


@router.get("/pending")
def pending(
    org_id: str | None = None,
    repo_id: str | None = None,
    limit: int = Query(default=50, le=100),
) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    with get_connection() as conn:
        items = MemoryRepo(conn).list_pending(org_id, repo_id, limit=limit)
    return {"items": [_public(i) for i in items]}


@router.get("/context")
def context(
    org_id: str | None = None,
    repo_id: str | None = None,
    limit: int = Query(default=12, le=25),
) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    return get_context(org_id, repo_id, limit=limit)


@router.get("/memories/{memory_id}")
def get_memory(memory_id: UUID, org_id: str | None = None, repo_id: str | None = None) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    with get_connection() as conn:
        row = MemoryRepo(conn).get(memory_id, org_id, repo_id)
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return _public(row)


@router.post("/memories/{memory_id}/confirm")
def confirm(memory_id: UUID, org_id: str | None = None, repo_id: str | None = None) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    try:
        with get_connection() as conn:
            row = MemoryRepo(conn).confirm(memory_id, org_id, repo_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return _public(row)


@router.post("/memories/{memory_id}/reject")
def reject(memory_id: UUID, org_id: str | None = None, repo_id: str | None = None) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    try:
        with get_connection() as conn:
            row = MemoryRepo(conn).reject(memory_id, org_id, repo_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return _public(row)


@router.post("/memories/{memory_id}/supersede")
def supersede(
    memory_id: UUID,
    body: SupersedeBody,
    org_id: str | None = None,
    repo_id: str | None = None,
) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    reason = deny_reason(body.statement)
    if reason:
        raise HTTPException(status_code=400, detail={"denied": reason})
    try:
        with get_connection() as conn:
            result = MemoryRepo(conn).supersede(
                memory_id,
                org_id,
                repo_id,
                statement=body.statement,
                rationale=body.rationale,
                category=body.category,
                tags=body.tags,
                polarity=body.polarity,
                actor=body.actor,
            )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return {"old": _public(result["old"]), "new": _public(result["new"])}


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
