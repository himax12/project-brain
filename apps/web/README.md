# HITL UI — talks only to FastAPI (never to CockroachDB directly).

## Run

1. Start the API from `apps/api` (`uv run uvicorn …`).
2. Copy `.env.example` to `.env.local`.
3. `npm install` then `npm run dev` → http://localhost:3000

Pages: `/pending` inbox · `/context` boot packet · `/recall` playground · `/memories/[id]` detail.
