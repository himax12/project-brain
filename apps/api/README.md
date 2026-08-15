# API package

```powershell
uv sync --extra dev
uv run pytest
uv run uvicorn project_brain.api.main:app --reload --app-dir src
uv run python -m project_brain.mcp.server
```
