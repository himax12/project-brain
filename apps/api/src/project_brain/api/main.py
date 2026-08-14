from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from project_brain.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Project Brain", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("project_brain.api.main:app", host="127.0.0.1", port=8000, reload=True)
