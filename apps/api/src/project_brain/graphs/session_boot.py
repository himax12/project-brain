from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from project_brain.db.events import append_event
from project_brain.db.memories import MemoryRepo
from project_brain.db.pool import get_connection
from project_brain.packets import boot_packet


class SessionBootState(TypedDict, total=False):
    org_id: str
    repo_id: str
    categories: list[str] | None
    limit: int
    rows: list[dict[str, Any]]
    packet: dict[str, Any]
    error: str | None


def validate_scope(state: SessionBootState) -> SessionBootState:
    if not state.get("org_id") or not state.get("repo_id"):
        return {**state, "error": "org_id and repo_id are required"}
    return state


def load_active(state: SessionBootState) -> SessionBootState:
    if state.get("error"):
        return state
    cap = min(max(int(state.get("limit") or 12), 1), 25)
    with get_connection() as conn:
        rows = MemoryRepo(conn).boot_active(
            state["org_id"],
            state["repo_id"],
            limit=cap,
            categories=state.get("categories"),
        )
        append_event(
            conn,
            org_id=state["org_id"],
            repo_id=state["repo_id"],
            event_type="boot_pack",
            payload={"count": len(rows)},
        )
    return {**state, "limit": cap, "rows": rows}


def format_packet(state: SessionBootState) -> SessionBootState:
    if state.get("error"):
        return {**state, "packet": {"query_intent": "error", "error": state["error"], "pin": [], "decide": []}}
    packet = boot_packet(list(state.get("rows") or []), limit=int(state.get("limit") or 12))
    return {**state, "packet": packet}


def build_boot_graph():
    g = StateGraph(SessionBootState)
    g.add_node("validate_scope", validate_scope)
    g.add_node("load_active", load_active)
    g.add_node("format_packet", format_packet)
    g.add_edge(START, "validate_scope")
    g.add_edge("validate_scope", "load_active")
    g.add_edge("load_active", "format_packet")
    g.add_edge("format_packet", END)
    return g.compile()


_GRAPH = None


def get_context(
    org_id: str,
    repo_id: str,
    *,
    limit: int = 12,
    categories: list[str] | None = None,
) -> dict:
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_boot_graph()
    result = _GRAPH.invoke(
        {
            "org_id": org_id,
            "repo_id": repo_id,
            "limit": limit,
            "categories": categories,
        }
    )
    return result.get("packet") or result
