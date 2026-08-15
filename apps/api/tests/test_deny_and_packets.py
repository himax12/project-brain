from __future__ import annotations

from project_brain.packets import boot_packet
from project_brain.services.deny_list import deny_reason


def test_deny_secret() -> None:
    assert deny_reason("here is my api_key=sk-abcdefghijklmnop") == "secret"


def test_deny_empty() -> None:
    assert deny_reason("   ") == "empty"


def test_allow_decision() -> None:
    assert deny_reason("Never perform sync HTTP Stripe retries.") is None


def test_boot_must_not_first() -> None:
    rows = [
        {
            "id": "a",
            "statement": "outbox",
            "polarity": "must",
            "importance": 0.9,
            "rationale": None,
            "category": "payments",
            "tags": [],
        },
        {
            "id": "b",
            "statement": "never sync",
            "polarity": "must_not",
            "importance": 0.5,
            "rationale": None,
            "category": "payments",
            "tags": [],
        },
    ]
    # packet split: must_not always pin; high importance also pin
    packet = boot_packet(rows, limit=12)
    pin_ids = [p["id"] for p in packet["pin"]]
    assert "b" in pin_ids
    assert "a" in pin_ids
