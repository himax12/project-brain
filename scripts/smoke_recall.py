from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from project_brain.config import get_settings  # noqa: E402
from project_brain.graphs.memory_recall import recall  # noqa: E402
from project_brain.graphs.session_boot import get_context  # noqa: E402
from project_brain.services.governance import confirm_and_embed, remember_decision  # noqa: E402


def main() -> None:
    s = get_settings()
    org, repo = s.default_org_id, s.default_repo_id
    created = remember_decision(
        org_id=org,
        repo_id=repo,
        statement="Never use Redis for billing cache.",
        polarity="must_not",
    )
    assert created.get("ok"), created
    confirm_and_embed(UUID(str(created["id"])), org, repo)
    packet = recall(org, repo, "Can we use Redis for billing cache?")
    assert packet.get("query_intent") in {"policy", "general"}, packet
    assert "pin" in packet and "decide" in packet and "do_not_use" in packet
    boot = get_context(org, repo)
    assert any("Redis" in p.get("statement", "") for p in boot.get("pin", []) + boot.get("decide", [])), boot
    print("smoke_recall OK")
    print(f"  intent={packet.get('query_intent')} pin={len(packet.get('pin') or [])} do_not_use={packet.get('do_not_use')}")


if __name__ == "__main__":
    main()
