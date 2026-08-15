from __future__ import annotations

from project_brain.packets import recall_packet
from project_brain.services.conflicts import find_conflicts
from project_brain.services.embeddings import cosine, stub_embed
from project_brain.services.extract import heuristic_extract
from project_brain.services.intent import route_intent


def test_intent_lookup_and_policy() -> None:
    assert route_intent("plan_id on Invoice") == "lookup_id"
    assert route_intent("Can we use Redis for billing cache?") == "policy"
    assert route_intent("what changed after we replaced the outbox") == "what_changed"
    assert route_intent("what did we try last session") == "episode"


def test_stub_embed_similar_text() -> None:
    a = stub_embed("Never use Redis for billing cache")
    b = stub_embed("Never use Redis for the billing cache layer")
    c = stub_embed("Prefer structured logging in workers")
    assert cosine(a, b) > cosine(a, c)


def test_heuristic_extract_never_line() -> None:
    items = heuristic_extract("chit chat\nNever sync HTTP Stripe retries.\nremind me to eat")
    assert any("Never sync" in i["statement"] for i in items)
    assert items[0]["polarity"] == "must_not"


def test_conflict_polarity_clash() -> None:
    hits = find_conflicts(
        "Always use Redis for billing cache",
        [{"id": "x", "statement": "Never use Redis for billing cache", "polarity": "must_not"}],
    )
    assert hits


def test_recall_packet_do_not_use_and_escalation() -> None:
    packet = recall_packet(
        intent="policy",
        pin=[{"id": "a", "authority": "must_obey", "statement": "never redis"}],
        decide=[],
        evidence=[],
        conflicts=[],
        do_not_use=["old"],
        density_high=True,
        query="Can we use Redis?",
    )
    assert packet["query_intent"] == "policy"
    assert "pin" in packet and "decide" in packet
    assert packet["do_not_use"] == ["old"]
    assert packet["escalation"]["reason"] == "ambiguous_near_duplicates"
    assert packet["meta"]["status_filter"] == "active"
