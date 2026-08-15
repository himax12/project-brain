from __future__ import annotations

from typing import Any


def boot_packet(rows: list[dict[str, Any]], *, limit: int) -> dict[str, Any]:
    pin: list[dict[str, Any]] = []
    decide: list[dict[str, Any]] = []
    for row in rows:
        item = _item(row)
        if row.get("polarity") == "must_not" or row.get("importance", 0) >= 0.7:
            item["authority"] = "must_obey"
            pin.append(item)
        else:
            item["authority"] = "active_decision"
            decide.append(item)
    return {
        "query_intent": "boot",
        "pin": pin,
        "decide": decide,
        "evidence": [],
        "conflicts": [],
        "do_not_use": [],
        "escalation": {
            "available": ["recall", "get_memory"],
            "reason": "boot_budget" if len(rows) >= limit else None,
        },
        "meta": {"count": len(rows), "status_filter": "active"},
    }


def recall_packet(
    *,
    intent: str,
    pin: list[dict[str, Any]],
    decide: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    do_not_use: list[str],
    density_high: bool,
    query: str,
) -> dict[str, Any]:
    reason = None
    if not pin and not decide and not evidence:
        reason = "no_hits"
    elif density_high:
        reason = "ambiguous_near_duplicates"
    elif conflicts:
        reason = "unresolved_conflict"
    elif intent == "episode" and evidence:
        reason = None
    available = ["get_memory", "search_chat"]
    return {
        "query_intent": intent,
        "query": query,
        "pin": pin,
        "decide": decide,
        "evidence": evidence,
        "conflicts": conflicts,
        "do_not_use": do_not_use,
        "escalation": {"available": available, "reason": reason},
        "meta": {
            "status_filter": "active",
            "density_high": density_high,
        },
    }


def scored_item(row: dict[str, Any], *, authority: str) -> dict[str, Any]:
    item = _item(row)
    item["authority"] = authority
    if row.get("score") is not None:
        item["score"] = float(row["score"])
    if row.get("why"):
        item["why"] = row["why"]
    return item


def _item(row: dict[str, Any]) -> dict[str, Any]:
    mid = str(row["id"])
    return {
        "id": mid,
        "authority": "must_obey",
        "polarity": row.get("polarity"),
        "statement": row["statement"],
        "rationale": row.get("rationale"),
        "category": row.get("category"),
        "tags": row.get("tags") or [],
        "cite": mid,
    }
