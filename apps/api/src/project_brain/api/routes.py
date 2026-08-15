from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from project_brain.api.deps import require_api_key
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


class RecallBody(BaseModel):
    query: str
    org_id: str | None = None
    repo_id: str | None = None
    intent_hint: str | None = None


class IngestBody(BaseModel):
    transcript: str
    session_id: str = "explicit"
    org_id: str | None = None
    repo_id: str | None = None
    actor: str | None = None


class IngestLocalBody(BaseModel):
    path: str | None = None
    org_id: str | None = None
    repo_id: str | None = None
    actor: str | None = None


class ResolveBody(BaseModel):
    pending_id: UUID
    existing_id: UUID
    choice: str = Field(description="keep_existing or switch_to_pending")
    org_id: str | None = None
    repo_id: str | None = None
    actor: str | None = None


def _scope(org_id: str | None, repo_id: str | None) -> tuple[str, str]:
    s = get_settings()
    return org_id or s.default_org_id, repo_id or s.default_repo_id


@router.post("/remember")
def remember(body: RememberBody) -> dict:
    org_id, repo_id = _scope(body.org_id, body.repo_id)
    result = remember_decision(
        org_id=org_id,
        repo_id=repo_id,
        statement=body.statement,
        rationale=body.rationale,
        category=body.category,
        tags=body.tags,
        polarity=body.polarity,
        actor=body.actor,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@router.get("/pending")
def pending(
    org_id: str | None = None,
    repo_id: str | None = None,
    limit: int = Query(default=50, le=100),
) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    with get_connection() as conn:
        items = MemoryRepo(conn).list_pending(org_id, repo_id, limit=limit)
    return {"items": [public_memory(i) for i in items]}


@router.get("/context")
def context(
    org_id: str | None = None,
    repo_id: str | None = None,
    limit: int = Query(default=12, le=25),
) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    return get_context(org_id, repo_id, limit=limit)


@router.post("/recall")
def recall_route(body: RecallBody) -> dict:
    org_id, repo_id = _scope(body.org_id, body.repo_id)
    return recall(org_id, repo_id, body.query, intent_hint=body.intent_hint)


@router.post("/ingest_session")
def ingest_route(body: IngestBody) -> dict:
    org_id, repo_id = _scope(body.org_id, body.repo_id)
    return ingest_session(
        org_id=org_id,
        repo_id=repo_id,
        transcript=body.transcript,
        session_id=body.session_id,
        actor=body.actor,
    )


@router.post("/ingest_local_chat")
def ingest_local_route(body: IngestLocalBody) -> dict:
    org_id, repo_id = _scope(body.org_id, body.repo_id)
    result = ingest_local_chat(
        org_id=org_id,
        repo_id=repo_id,
        path=body.path,
        actor=body.actor,
    )
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result)
    return result


@router.post("/resolve_conflict")
def resolve_conflict(body: ResolveBody) -> dict:
    org_id, repo_id = _scope(body.org_id, body.repo_id)
    if body.choice not in {"keep_existing", "switch_to_pending"}:
        raise HTTPException(status_code=400, detail="choice must be keep_existing or switch_to_pending")
    try:
        with get_connection() as conn:
            repo = MemoryRepo(conn)
            if body.choice == "keep_existing":
                row = repo.reject(body.pending_id, org_id, repo_id, actor=body.actor)
                return {"ok": True, "choice": body.choice, "rejected": public_memory(row)}
            result = repo.resolve_switch(
                body.pending_id, body.existing_id, org_id, repo_id, actor=body.actor
            )
            try:
                repo.set_embedding(result["new"]["id"], embed_text(str(result["new"]["statement"])))
            except Exception:
                pass
            return {
                "ok": True,
                "choice": body.choice,
                "old": public_memory(result["old"]),
                "new": public_memory(result["new"]),
            }
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get("/chat")
def search_chat(
    q: str,
    org_id: str | None = None,
    repo_id: str | None = None,
    session_id: str | None = None,
) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    with get_connection() as conn:
        items = ChatRepo(conn).search(org_id, repo_id, q, session_id=session_id)
    return {"items": [public_chat(i) for i in items]}


@router.get("/memories/{memory_id}")
def get_memory(memory_id: UUID, org_id: str | None = None, repo_id: str | None = None) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    with get_connection() as conn:
        row = MemoryRepo(conn).get(memory_id, org_id, repo_id)
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    return public_memory(row)


@router.post("/memories/{memory_id}/confirm")
def confirm(memory_id: UUID, org_id: str | None = None, repo_id: str | None = None) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    try:
        return confirm_and_embed(memory_id, org_id, repo_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.post("/memories/{memory_id}/reject")
def reject(memory_id: UUID, org_id: str | None = None, repo_id: str | None = None) -> dict:
    org_id, repo_id = _scope(org_id, repo_id)
    try:
        with get_connection() as conn:
            row = MemoryRepo(conn).reject(memory_id, org_id, repo_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return public_memory(row)


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
            try:
                MemoryRepo(conn).set_embedding(
                    result["new"]["id"], embed_text(body.statement)
                )
            except Exception:
                pass
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    return {"old": public_memory(result["old"]), "new": public_memory(result["new"])}
