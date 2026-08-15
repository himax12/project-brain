from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from project_brain.config import get_settings  # noqa: E402
from project_brain.services.governance import ingest_local_chat  # noqa: E402


def main() -> None:
    s = get_settings()
    path = sys.argv[1] if len(sys.argv) > 1 else None
    result = ingest_local_chat(
        org_id=s.default_org_id,
        repo_id=s.default_repo_id,
        path=path,
    )
    print(result)


if __name__ == "__main__":
    main()
