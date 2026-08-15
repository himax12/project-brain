from project_brain.graphs.session_boot import format_packet, validate_scope
from project_brain.graphs.memory_recall import validate as recall_validate
from project_brain.graphs.session_boot import build_boot_graph
from project_brain.graphs.memory_recall import build_recall_graph


def test_boot_graph_compiles() -> None:
    g = build_boot_graph()
    assert g is not None


def test_recall_graph_compiles() -> None:
    g = build_recall_graph()
    assert g is not None


def test_boot_validate_requires_scope() -> None:
    out = validate_scope({"org_id": "", "repo_id": "billing"})
    assert out.get("error")


def test_boot_format_must_not_pin() -> None:
    packet = format_packet(
        {
            "limit": 12,
            "rows": [
                {
                    "id": "b",
                    "statement": "never sync",
                    "polarity": "must_not",
                    "importance": 0.4,
                    "rationale": None,
                    "category": None,
                    "tags": [],
                }
            ],
        }
    )["packet"]
    assert packet["pin"][0]["id"] == "b"


def test_recall_validate_query() -> None:
    out = recall_validate({"org_id": "acme", "repo_id": "billing", "query": "  "})
    assert out.get("error")
