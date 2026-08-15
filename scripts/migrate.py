from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

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


def apply_file(conn, path: Path, *, optional: bool = False) -> None:
    sql = path.read_text(encoding="utf-8")
    for stmt in _statements(sql):
        try:
            conn.execute(stmt)
        except Exception as exc:
            if optional:
                print(f"skip optional {path.name}: {exc}")
                conn.rollback()
                return
            raise
    conn.commit()
    print(f"applied {path}")


def main() -> None:
    conn = connect()
    try:
        apply_file(conn, ROOT / "sql" / "001_schema.sql")
        apply_file(conn, ROOT / "sql" / "002_vector_index.sql", optional=True)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
