# Devpost draft — Project Brain

**Hackathon:** CockroachDB × AWS  
**Repo:** https://github.com/himax12/project-brain *(make public before submit)*  
**License:** MIT

## Elevator

Coding agents forget project law every session. Project Brain stores **decisions** (not chat logs) in CockroachDB, serves them as **authority packets** (pin / decide / do_not_use), and requires a human confirm before anything becomes law.

## What the agent does with memory

1. Session start: `get_context` loads **active** decisions; `must_not` pins first.
2. Mid-task: `recall` returns a routed packet (policy vs identifier vs episode), not a flat score list.
3. Modify: `supersede` / `resolve_conflict` marks the old row `invalid_at` so it cannot be reused as law.
4. Explicit `ingest_session` may **propose** candidates; they stay `pending_review` until confirm.

## Tools named for eligibility

- **CockroachDB 1:** Distributed **VECTOR(1024)** index on `memories.embedding`
- **CockroachDB 2:** **Managed MCP Server** (SQL against the same cluster on camera)
- **AWS:** Amazon **Bedrock** — Titan Text Embeddings V2 (confirm/recall) + Claude Haiku (explicit extract)

## How to test

```text
clone → set DATABASE_URL in .env → uv sync → migrate.py → smoke_v0.py
→ uvicorn FastAPI → npm run dev in apps/web
→ remember → confirm in UI → new Cursor chat get_context
→ recall "Can we use Redis for billing cache?"
→ Managed MCP SELECT active rows
```

Without AWS: `EMBED_STUB=1` (default) still writes 1024-d vectors so VECTOR + packets work.

## Video script (< 3 min)

1. Empty pending inbox / empty `SELECT`.
2. Save “Never sync HTTP Stripe retries” → confirm in Next.js.
3. New Cursor chat: `get_context` shows pin first.
4. `recall` packet JSON on `/recall`.
5. Supersede → old id in `do_not_use`.
6. Managed MCP `SELECT` shows the CockroachDB row.
