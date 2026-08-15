from __future__ import annotations

import re

_SECRET = re.compile(
    r"(api[_-]?key|secret|password|token|bearer\s+[a-z0-9]|sk-[a-z0-9]{10,}"
    r"|AKIA[0-9A-Z]{16})",
    re.I,
)
_PREF = re.compile(
    r"\b(i prefer|my favorite|please remember i like|dark mode)\b",
    re.I,
)
_TASK = re.compile(
    r"\b(todo|fix this later|one-off|remind me to)\b",
    re.I,
)


def deny_reason(statement: str) -> str | None:
    text = statement.strip()
    if not text:
        return "empty"
    if _SECRET.search(text):
        return "secret"
    if _PREF.search(text) and len(text) < 120:
        return "pref"
    if _TASK.search(text) and "decision" not in text.lower():
        return "task"
    return None
