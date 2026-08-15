from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

_USER_QUERY = re.compile(r"<user_query>\s*(.*?)\s*</user_query>", re.S | re.I)
_TOOL_NOISE = re.compile(r"<timestamp>.*?</timestamp>", re.S)


def default_transcript_dir() -> Path:
    override = os.environ.get("CURSOR_TRANSCRIPTS_DIR", "").strip()
    if override:
        return Path(override)
    home = Path.home()
    # Cursor stores agent chats per workspace under .cursor/projects/<slug>/agent-transcripts
    projects = home / ".cursor" / "projects"
    slug = "c-Users-ghima-Desktop-project-brain"
    return projects / slug / "agent-transcripts"


def latest_transcript_path(root: Path | None = None) -> Path | None:
    base = root or default_transcript_dir()
    if not base.exists():
        return None
    files = sorted(base.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def parse_chat_file(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return parse_jsonl(text)
    if suffix == ".json":
        return parse_json_export(text)
    return [{"role": "user", "content": _clean(text)}]


def parse_jsonl(text: str) -> list[dict[str, str]]:
    turns: list[dict[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        turn = _turn_from_obj(obj)
        if turn:
            turns.append(turn)
    return turns


def parse_json_export(text: str) -> list[dict[str, str]]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return [{"role": "user", "content": _clean(text)}]
    if isinstance(data, list):
        out: list[dict[str, str]] = []
        for obj in data:
            if isinstance(obj, dict):
                turn = _turn_from_obj(obj)
                if turn:
                    out.append(turn)
        return out
    if isinstance(data, dict):
        mapping = data.get("mapping") or data.get("messages")
        if isinstance(mapping, list):
            return parse_json_export(json.dumps(mapping))
        if isinstance(mapping, dict):
            turns: list[dict[str, str]] = []
            for node in mapping.values():
                if not isinstance(node, dict):
                    continue
                msg = node.get("message") or node
                turn = _turn_from_obj(msg if isinstance(msg, dict) else {})
                if turn:
                    turns.append(turn)
            return turns
    return [{"role": "user", "content": _clean(text)}]


def extract_corpus(turns: list[dict[str, str]], *, max_chars: int = 24_000) -> str:
    """User turns + decision-like assistant lines only — not full agent tool dumps."""
    chunks: list[str] = []
    for turn in turns:
        content = turn.get("content") or ""
        role = turn.get("role") or "user"
        if role == "user":
            chunks.append(content)
            continue
        for line in content.splitlines():
            low = line.lower().strip()
            if low.startswith(("never ", "always ", "must ", "we decided", "decision:")):
                chunks.append(line.strip())
    blob = "\n".join(chunks)
    return blob[-max_chars:]


def _turn_from_obj(obj: dict[str, Any]) -> dict[str, str] | None:
    role = str(obj.get("role") or obj.get("author") or "user").lower()
    if role in {"assistant", "model", "bot"}:
        role = "assistant"
    elif role not in {"user", "system"}:
        role = "user"
    raw = _content_text(obj.get("message") if isinstance(obj.get("message"), dict) else obj)
    cleaned = _clean(raw)
    if not cleaned:
        return None
    if role == "assistant" and len(cleaned) > 4000:
        cleaned = cleaned[:4000]
    return {"role": role, "content": cleaned}


def _content_text(obj: dict[str, Any]) -> str:
    content = obj.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") in {None, "text"}:
                parts.append(str(block.get("text") or ""))
        return "\n".join(parts)
    if obj.get("text"):
        return str(obj["text"])
    return ""


def _clean(text: str) -> str:
    if not text:
        return ""
    m = _USER_QUERY.search(text)
    if m:
        text = m.group(1)
    text = _TOOL_NOISE.sub("", text)
    return text.strip()
