from __future__ import annotations

import json
import re
from typing import Any

from project_brain.config import get_settings
from project_brain.services.deny_list import deny_reason

_DECISION = re.compile(
    r"^\s*(?:we (?:decided|chose)|decision:|never |always |must |do not |don't )\s*(.+)$",
    re.I,
)


def extract_candidates(transcript: str) -> list[dict[str, Any]]:
    """Lean E: explicit ingest only. Never auto-activates."""
    settings = get_settings()
    if settings.embed_stub or not settings.bedrock_chat_model:
        raw = heuristic_extract(transcript)
    else:
        raw = bedrock_extract(transcript)
    out: list[dict[str, Any]] = []
    for item in raw:
        statement = str(item.get("statement") or "").strip()
        if not statement:
            continue
        denied = deny_reason(statement)
        if denied:
            continue
        polarity = item.get("polarity") or "must"
        if polarity not in {"must", "must_not", "advisory"}:
            polarity = "must"
        out.append(
            {
                "statement": statement,
                "rationale": item.get("rationale"),
                "category": item.get("category"),
                "polarity": polarity,
                "confidence": float(item.get("confidence") or 0.6),
            }
        )
    return out


def heuristic_extract(transcript: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for line in transcript.splitlines():
        line = line.strip().lstrip("-*").strip()
        m = _DECISION.match(line)
        if not m and line.lower().startswith(("never ", "always ", "must ")):
            statement = line
        elif m:
            statement = line
        else:
            continue
        polarity = "must_not" if statement.lower().startswith(("never", "do not", "don't")) else "must"
        found.append({"statement": statement, "polarity": polarity, "confidence": 0.55})
    return found


def bedrock_extract(transcript: str) -> list[dict[str, Any]]:
    settings = get_settings()
    import boto3

    client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    prompt = (
        "Extract lasting PROJECT DECISIONS from this coding-agent transcript. "
        "Return JSON {\"candidates\":[{\"statement\",\"rationale\",\"category\","
        "\"polarity\":\"must|must_not|advisory\",\"confidence\":0-1}]}. "
        "Skip prefs, secrets, one-off todos, chit-chat.\n\n"
        f"{transcript[:12000]}"
    )
    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        }
    )
    resp = client.invoke_model(
        modelId=settings.bedrock_chat_model,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    payload = json.loads(resp["body"].read())
    text = ""
    for block in payload.get("content") or []:
        if block.get("type") == "text":
            text += block.get("text") or ""
    return _parse_json_candidates(text)


def _parse_json_candidates(text: str) -> list[dict[str, Any]]:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0:
        return []
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return []
    return list(data.get("candidates") or [])
