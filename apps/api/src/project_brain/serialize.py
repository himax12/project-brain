from __future__ import annotations

from typing import Any


def public_memory(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["id"] = str(out["id"])
    if out.get("supersedes_id"):
        out["supersedes_id"] = str(out["supersedes_id"])
    out.pop("embedding", None)
    for key in ("created_at", "updated_at", "invalid_at"):
        if out.get(key) is not None:
            out[key] = out[key].isoformat()
    return out


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{x:.8f}" for x in values) + "]"
