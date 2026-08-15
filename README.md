# Project Brain

Governed **project decisions** for coding agents (Cursor / Claude). CockroachDB is the source of truth. Agents **retrieve, reuse, and modify** decisions through MCP; humans confirm in a Next.js inbox.

This is a **connector over the chatbot**, not a replacement chat UI.

## One-sentence demo

Empty brain → save a decision → confirm → **new session reuses it** (`must_not` pins first) → mid-task **recall packet** → **supersede** → recall shows the old id in `do_not_use` → the row is visible in CockroachDB (SQL or Managed MCP).

## Stack

| Layer | Choice |
|---|---|
| Package manager | **uv** (Python 3.12) |
| API | **FastAPI** |
| UI | **Next.js 15** (App Router) — Node 22 LTS |
| Agent | Memory MCP (stdio) |
| Workflow | **LangGraph** (`session_boot`, `memory_recall`) |
| DB | **CockroachDB Cloud** `VECTOR(1024)` + **Managed MCP** |
| AWS | **Bedrock** Titan Text Embeddings V2 (1024) + Claude Haiku extract |
| Lean pack | **E** explicit extract only · **B** `must_not` pins first · **F** `invalid_at` on supersede |

```text
Cursor MCP ──in-process──► Python package (db / graphs / services)
Next.js    ──HTTP────────► FastAPI ──► same package
                                 ▼
                    CockroachDB Cloud  (+ Bedrock on confirm/extract)
```

**CockroachDB tools used:** Distributed **VECTOR** indexing · **Managed MCP** (second server in `configs/mcp.json.example`).  
**AWS service used:** Amazon **Bedrock**. Set `EMBED_STUB=1` to run without AWS (deterministic stub vectors).

## Layout

```text
apps/api     uv Python — FastAPI + MCP + LangGraph
apps/web     Next.js HITL (pending / context / recall)
sql/         001_schema.sql, 002_vector_index.sql
scripts/     migrate.py, smoke_v0.py, setup_crdb.ps1
docker-compose.yml
configs/     mcp.json.example
```

## Setup

### A. Local CockroachDB (fastest)

```powershell
cd C:\Users\ghima\Desktop\project-brain
docker compose up -d
# or: powershell -File scripts\setup_crdb.ps1
copy .env.example .env
```

`.env` default URL is `postgresql://root@localhost:26257/defaultdb?sslmode=disable`. UI on http://localhost:8081.

### B. CockroachDB Cloud

Create a cluster, copy the Postgres URL into `.env` as `DATABASE_URL` (`sslmode=verify-full`).

Then migrate and smoke:

```powershell
cd C:\Users\ghima\Desktop\project-brain\apps\api
uv sync --extra dev
uv run python ..\..\scripts\migrate.py
uv run python ..\..\scripts\smoke_v0.py
uv run pytest
```

API:

```powershell
uv run uvicorn project_brain.api.main:app --reload --app-dir src
```

- Health: http://127.0.0.1:8000/healthz  
- Swagger: http://127.0.0.1:8000/docs — header `X-API-Key: dev-local-key-change-me`

UI (Node 22):

```powershell
cd C:\Users\ghima\Desktop\project-brain\apps\web
copy .env.example .env.local
npm install
npm run dev
```

http://localhost:3000 → pending inbox.

### MCP (Cursor)

Copy `configs/mcp.json.example` into Cursor MCP settings. Fix `--directory` to this clone. Paste **Cockroach Managed MCP** URL/token from the Cloud console into the `cockroachdb` server block.

Restart Cursor, then:

1. `remember` with `polarity=must_not`
2. `confirm_memory`
3. New chat: `get_context` — never-X should pin first
4. `recall` with a policy question — packet, not a flat list
5. Managed MCP: `SELECT id, statement, status FROM memories WHERE status = 'active';`

### Local chat → memory (Cursor / Claude / GPT)

Chat windows stay **local evidence**. CockroachDB stays **law**.

```powershell
# MCP (after reload): ingest_local_chat
# or HTTP:
# POST /v1/ingest_local_chat  { "path": "optional.jsonl" }
# empty path = newest file under %USERPROFILE%\.cursor\projects\...\agent-transcripts
```

Then confirm in http://localhost:3000/pending. Episode recall can `search_chat` those stored turns; they never get `must_obey` until confirmed.

### CockroachDB Skills (optional maximize)

```powershell
npx skills add cockroachlabs/cockroachdb-skills
```

Use Skills while writing SQL / VECTOR DDL; Project Brain still owns product memory.

## Memory rules

| Path | Behavior |
|---|---|
| Extract / remember | Always `pending_review` (Lean E) |
| Confirm | `active` + embedding (Titan or stub) |
| `get_context` | `status = active` only, `must_not` first (Lean B) |
| Supersede | old `invalid_at` + `superseded`; recall `do_not_use` (Lean F) |
| Deny-list | secrets, prefs, one-off tasks never become pending |
| Conflict | overlapping / polarity clash stays pending until `resolve_conflict` |

## Video / Devpost

See [DEVPOST.md](./DEVPOST.md), [docs/THREAT_MODEL.md](./docs/THREAT_MODEL.md), and [video/SCRIPT.md](./video/SCRIPT.md). License: [MIT](./LICENSE).

Repo is private until you switch it public for submission: `gh repo edit himax12/project-brain --visibility public`.
