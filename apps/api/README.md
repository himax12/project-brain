# apps/api

Python package: FastAPI + MCP + CockroachDB spine.

```powershell
cd C:\Users\ghima\Desktop\project-brain
copy .env.example .env   # set DATABASE_URL
cd apps\api
uv sync --extra dev
uv run python ..\..\scripts\migrate.py
uv run python ..\..\scripts\smoke_v0.py
uv run pytest
uv run uvicorn project_brain.api.main:app --reload --app-dir src
```

Swagger: http://127.0.0.1:8000/docs  (header `X-API-Key`)

MCP: see `configs/mcp.json.example`
