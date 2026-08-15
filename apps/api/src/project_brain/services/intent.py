from __future__ import annotations

import re

_IDISH = re.compile(
    r"\b([a-z]+_[a-z0-9]+|[A-Z][a-zA-Z]+Error|ECONNREFUSED|\.tsx?|\.py)\b"
)
_POLICY = re.compile(
    r"\b(can we|should we|never|allowed|policy|must not|must we|is it ok)\b",
    re.I,
)
_CHANGED = re.compile(r"\b(what changed|after we|instead of|supersed|replace[d]?)\b", re.I)
_EPISODE = re.compile(r"\b(last session|we tried|transcript|what did we say|chat)\b", re.I)


def route_intent(query: str, hint: str | None = None) -> str:
    if hint in {"boot", "policy", "lookup_id", "what_changed", "episode", "general"}:
        return hint
    q = query.strip()
    if _IDISH.search(q):
        return "lookup_id"
    if _CHANGED.search(q):
        return "what_changed"
    if _EPISODE.search(q):
        return "episode"
    if _POLICY.search(q):
        return "policy"
    return "general"
