from __future__ import annotations

from typing import Any

_NEG = {"never", "dont", "don't", "must_not", "forbidden", "no"}
_POS = {"must", "always", "require", "use"}


def token_set(text: str) -> set[str]:
    return {
        t
        for t in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split()
        if len(t) > 2
    }


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def polarity_clash(statement: str, other: dict[str, Any]) -> bool:
    a = token_set(statement)
    b = token_set(str(other.get("statement") or ""))
    a_neg = bool(a & _NEG) or other.get("polarity") == "must_not" and False
    stmt_neg = bool(a & _NEG)
    other_neg = bool(b & _NEG) or other.get("polarity") == "must_not"
    if stmt_neg != other_neg and jaccard(a - _NEG - _POS, b - _NEG - _POS) >= 0.25:
        return True
    return False


def find_conflicts(statement: str, actives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tokens = token_set(statement)
    hits: list[dict[str, Any]] = []
    for row in actives:
        other = token_set(str(row.get("statement") or ""))
        score = jaccard(tokens, other)
        clash = polarity_clash(statement, row)
        if score >= 0.45 or clash:
            hits.append(
                {
                    "id": str(row["id"]),
                    "statement": row.get("statement"),
                    "polarity": row.get("polarity"),
                    "overlap": round(score, 3),
                    "polarity_clash": clash,
                }
            )
    return hits
