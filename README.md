# Project Brain

Governed project memory for coding agents: **retrieve / reuse / modify** decisions in CockroachDB.

**Phase:** 1 spine (schema + SQL + FastAPI + MCP). Next.js UI is Phase 3.

## Stack

| Layer | Choice |
|---|---|
| Package manager | **uv** |
| API | **FastAPI** |
| UI | **Next.js** (`apps/web`, Phase 3) |
| Agent | Memory MCP (stdio) |
| DB | CockroachDB Cloud + `VECTOR(1024)` |
| Lean pack | E explicit extract · B `must_not` pins · F `invalid_at` |

## Layout

```text
apps/api     Python (uv) — FastAPI + MCP + db
apps/web     Next.js — HITL UI (Phase 3)
sql/         001_schema.sql
scripts/     migrate.py, smoke_v0.py
configs/     mcp.json.example
```

```text
Next.js ──HTTP──► FastAPI ──► db / graphs / services
MCP     ──in-process──► same package
                         ▼
                    CockroachDB
```

## Run (Phase 1)

```powershell
cd C:\Users\ghima\Desktop\project-brain
copy .env.example .env
# edit .env → DATABASE_URL from CockroachDB Cloud

cd apps\api
uv sync --extra dev
uv run python ..\..\scripts\migrate.py
uv run python ..\..\scripts\smoke_v0.py
uv run pytest
uv run uvicorn project_brain.api.main:app --reload --app-dir src
```

- Health: http://127.0.0.1:8000/healthz  
- Swagger: http://127.0.0.1:8000/docs — send header `X-API-Key: dev-local-key-change-me`

### MCP (Cursor)

Copy `configs/mcp.json.example` into Cursor MCP config. Restart Cursor, then:

1. `remember` with `polarity=must_not`  
2. `confirm_memory`  
3. New chat: `get_context` — never-X should pin first  

## Gate

Do not start Next.js until you sign Phase 1 (and Phase 2) in the planning repo `phases/GATES.md`.
