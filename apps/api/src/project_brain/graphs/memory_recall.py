from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from project_brain.db.chat import ChatRepo
from project_brain.db.memories import MemoryRepo
from project_brain.db.pool import get_connection
from project_brain.packets import recall_packet, scored_item
from project_brain.services.embeddings import density_high as density_flag
from project_brain.services.embeddings import embed_text
from project_brain.services.intent import route_intent


class MemoryRecallState(TypedDict, total=False):
    org_id: str
    repo_id: str
    query: str
    intent_hint: str | None
    intent: str
    query_embedding: list[float] | None
    candidates: list[dict[str, Any]]
    pin: list[dict[str, Any]]
    decide: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    conflicts: list[dict[str, Any]]
    do_not_use: list[str]
    density_high: bool
    packet: dict[str, Any]
    error: str | None


def validate(state: MemoryRecallState) -> MemoryRecallState:
    if not state.get("org_id") or not state.get("repo_id") or not str(state.get("query") or "").strip():
        return {**state, "error": "org_id, repo_id, and query are required"}
    return state


def route(state: MemoryRecallState) -> MemoryRecallState:
    if state.get("error"):
        return state
    intent = route_intent(state["query"], state.get("intent_hint"))
    return {**state, "intent": intent}


def search(state: MemoryRecallState) -> MemoryRecallState:
    if state.get("error"):
        return state
    query = state["query"]
    embedding = embed_text(query)
    with get_connection() as conn:
        repo = MemoryRepo(conn)
        candidates = repo.search_active(
            state["org_id"],
            state["repo_id"],
            query,
            embedding,
            limit=8,
        )
        superseded = repo.search_superseded(state["org_id"], state["repo_id"], query)
        chat_hits: list[dict[str, Any]] = []
        if state.get("intent") == "episode" or not candidates:
            chat_hits = ChatRepo(conn).search(
                state["org_id"], state["repo_id"], query, limit=5
            )
    do_not_use = [str(r["id"]) for r in superseded]
    evidence = [
        {
            "id": str(msg["id"]),
            "authority": "evidence",
            "statement": msg.get("content"),
            "cite": str(msg["id"]),
            "session_id": msg.get("session_id"),
        }
        for msg in chat_hits
    ]
    return {
        **state,
        "query_embedding": embedding,
        "candidates": candidates,
        "do_not_use": do_not_use,
        "evidence": evidence,
    }


def assemble(state: MemoryRecallState) -> MemoryRecallState:
    if state.get("error"):
        return {
            **state,
            "packet": {
                "query_intent": "error",
                "error": state["error"],
                "pin": [],
                "decide": [],
                "evidence": [],
                "conflicts": [],
                "do_not_use": [],
            },
        }
    intent = state.get("intent") or "general"
    candidates = list(state.get("candidates") or [])
    vectors = []
    for row in candidates:
        emb = row.get("embedding")
        if isinstance(emb, list):
            vectors.append(emb)
    dense = density_flag(vectors) if len(vectors) >= 2 else False
    if dense:
        candidates.sort(key=lambda r: (0 if r.get("why") == "fts" else 1, -float(r.get("score") or 0)))
    pin: list[dict[str, Any]] = []
    decide: list[dict[str, Any]] = []
    for row in candidates:
        if row.get("status") != "active":
            continue
        if intent == "policy" and (
            row.get("polarity") == "must_not" or float(row.get("importance") or 0) >= 0.7
        ):
            pin.append(scored_item(row, authority="must_obey"))
        elif row.get("polarity") == "must_not" and intent in {"policy", "general"}:
            pin.append(scored_item(row, authority="must_obey"))
        else:
            decide.append(scored_item(row, authority="active_decision"))
    evidence = list(state.get("evidence") or [])
    packet = recall_packet(
        intent=intent,
        pin=pin[:5],
        decide=decide[:5],
        evidence=evidence,
        conflicts=[],
        do_not_use=list(state.get("do_not_use") or []),
        density_high=dense,
        query=state["query"],
    )
    return {**state, "density_high": dense, "pin": pin, "decide": decide, "evidence": evidence, "packet": packet}


def build_recall_graph():
    g = StateGraph(MemoryRecallState)
    g.add_node("validate", validate)
    g.add_node("route", route)
    g.add_node("search", search)
    g.add_node("assemble", assemble)
    g.add_edge(START, "validate")
    g.add_edge("validate", "route")
    g.add_edge("route", "search")
    g.add_edge("search", "assemble")
    g.add_edge("assemble", END)
    return g.compile()


_GRAPH = None


def recall(
    org_id: str,
    repo_id: str,
    query: str,
    *,
    intent_hint: str | None = None,
) -> dict[str, Any]:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_recall_graph()
    result = _GRAPH.invoke(
        {
            "org_id": org_id,
            "repo_id": repo_id,
            "query": query,
            "intent_hint": intent_hint,
        }
    )
    return result.get("packet") or result
