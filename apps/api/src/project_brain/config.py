from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# repo root: project-brain/ (three levels up from this file: config.py → project_brain → src → api → apps → root)
_REPO_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    api_key: str = "dev-local-key-change-me"
    default_org_id: str = "acme"
    default_repo_id: str = "billing"
    embed_stub: bool = True
    embed_dim: int = 1024
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_embed_model: str = "amazon.titan-embed-text-v2:0"
    bedrock_chat_model: str = ""

    @property
    def repo_root(self) -> Path:
        return _REPO_ROOT

    @property
    def schema_path(self) -> Path:
        return _REPO_ROOT / "sql" / "001_schema.sql"


@lru_cache
def get_settings() -> Settings:
    return Settings()
