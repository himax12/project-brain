from __future__ import annotations

from pathlib import Path

from project_brain.services.local_chat import extract_corpus, parse_chat_file, parse_jsonl


def test_parse_cursor_jsonl_user_query() -> None:
    raw = (
        '{"role":"user","message":{"content":[{"type":"text","text":'
        '"<user_query>Never sync HTTP Stripe retries.</user_query>"}]}}\n'
        '{"role":"assistant","message":{"content":[{"type":"text","text":'
        '"We decided billing retries go through the outbox."}]}}\n'
    )
    turns = parse_jsonl(raw)
    assert turns[0]["role"] == "user"
    assert "Never sync" in turns[0]["content"]
    assert "<user_query>" not in turns[0]["content"]
    corpus = extract_corpus(turns)
    assert "Never sync" in corpus
    assert "outbox" in corpus


def test_parse_file_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "chat.jsonl"
    p.write_text(
        '{"role":"user","content":"Always use VECTOR(1024) for embeddings."}\n',
        encoding="utf-8",
    )
    turns = parse_chat_file(p)
    assert turns[0]["content"].startswith("Always use VECTOR")
