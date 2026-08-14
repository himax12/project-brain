from __future__ import annotations

from project_brain.db.memories import MemoryRepo
from project_brain.db.pool import get_connection
from project_brain.packets import boot_packet


def get_context(
    org_id: str,
    repo_id: str,
    *,
    limit: int = 12,
    categories: list[str] | None = None,
) -> dict:
    cap = min(max(limit, 1), 25)
    with get_connection() as conn:
        rows = MemoryRepo(conn).boot_active(
            org_id, repo_id, limit=cap, categories=categories
        )
    return boot_packet(rows, limit=cap)
