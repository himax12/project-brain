from __future__ import annotations

import hashlib
import json
import math

from project_brain.config import get_settings


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    dim = settings.embed_dim
    if settings.embed_stub:
        return stub_embed(text, dim=dim)
    return titan_embed(text, dim=dim)


def stub_embed(text: str, *, dim: int = 1024) -> list[float]:
    """Deterministic bag-of-ngrams vector so recall works without Bedrock."""
    vec = [0.0] * dim
    tokens = _tokens(text)
    grams = tokens + [f"{a}_{b}" for a, b in zip(tokens, tokens[1:])]
    for gram in grams:
        digest = hashlib.sha256(gram.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    return _l2(vec)


def titan_embed(text: str, *, dim: int = 1024) -> list[float]:
    settings = get_settings()
    import boto3

    client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
    body = json.dumps(
        {
            "inputText": text[:8000],
            "dimensions": dim,
            "normalize": True,
        }
    )
    resp = client.invoke_model(
        modelId=settings.bedrock_embed_model,
        contentType="application/json",
        accept="application/json",
        body=body,
    )
    payload = json.loads(resp["body"].read())
    embedding = payload.get("embedding")
    if not embedding:
        raise RuntimeError("Bedrock Titan returned no embedding")
    if len(embedding) != dim:
        raise RuntimeError(f"expected dim {dim}, got {len(embedding)}")
    return [float(x) for x in embedding]


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def density_high(vectors: list[list[float]], *, tau: float = 0.85) -> bool:
    if len(vectors) < 2:
        return False
    scores: list[float] = []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            scores.append(cosine(vectors[i], vectors[j]))
    return (sum(scores) / len(scores)) > tau


def _tokens(text: str) -> list[str]:
    return [t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if t]


def _l2(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]
