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
