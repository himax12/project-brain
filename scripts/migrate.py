from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from project_brain.config import get_settings  # noqa: E402
from project_brain.db.pool import connect  # noqa: E402


def _statements(sql: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(buf).strip()
            if stmt:
                parts.append(stmt)
            buf = []
    tail = "\n".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def main() -> None:
    settings = get_settings()
    sql = settings.schema_path.read_text(encoding="utf-8")
    conn = connect()
    try:
        for stmt in _statements(sql):
            conn.execute(stmt)
        conn.commit()
        print(f"applied {settings.schema_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
