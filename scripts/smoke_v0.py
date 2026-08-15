from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from project_brain.config import get_settings  # noqa: E402
from project_brain.db.memories import MemoryRepo  # noqa: E402
from project_brain.db.pool import get_connection  # noqa: E402
from project_brain.graphs.session_boot import get_context  # noqa: E402
from project_brain.services.deny_list import deny_reason  # noqa: E402


def main() -> None:
    s = get_settings()
    org, repo = s.default_org_id, s.default_repo_id
    secret = deny_reason("api_key=sk-abcdefghijklmnop")
    assert secret == "secret", secret

    with get_connection() as conn:
        repo_db = MemoryRepo(conn)
        must_not = repo_db.insert_pending(
            org_id=org,
            repo_id=repo,
            statement="Never perform sync HTTP Stripe retries.",
            polarity="must_not",
            importance=0.9,
        )
        must = repo_db.insert_pending(
            org_id=org,
            repo_id=repo,
            statement="Billing Stripe retries go through the outbox.",
            polarity="must",
            importance=0.8,
        )
        boot_before = repo_db.boot_active(org, repo)
        pending_ids = {str(r["id"]) for r in boot_before}
        assert str(must_not["id"]) not in pending_ids, "pending leaked into boot"
        repo_db.confirm(must_not["id"], org, repo)
        repo_db.confirm(must["id"], org, repo)

    packet = get_context(org, repo, limit=12)
    pin_ids = [p["id"] for p in packet["pin"]]
    assert str(must_not["id"]) in pin_ids, packet
    assert pin_ids[0] == str(must_not["id"]), f"must_not should be first: {pin_ids}"
    print("smoke_v0 OK")
    print(f"  pending hidden from boot")
    print(f"  confirmed {must_not['id']} (must_not) then {must['id']} (must)")
    print(f"  pin[0]={packet['pin'][0]['statement'][:48]}...")


if __name__ == "__main__":
    main()
