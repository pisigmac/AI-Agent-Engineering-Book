import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from interviewbank import load_bank, categories, search, get_by_category, get_by_difficulty


def test_load_count():
    bank = load_bank()
    assert len(bank) >= 1270


def test_categories_minimum_100():
    cats = categories()
    for slug in (
        "python",
        "machine_learning",
        "system_design",
        "ai_engineering",
        "generative_ai",
        "prompt_engineering",
        "context_engineering",
        "loop_engineering",
        "agent_frameworks",
        "agentic_ai",
        "behavioral"
    ):
        assert cats.get(slug, 0) >= 100, slug


def test_search_rag():
    hits = search("RAG")
    assert hits
    assert any("rag" in h.question.lower() or "rag" in h.answer.lower() for h in hits)


def test_get_by_category():
    py = get_by_category("python")
    assert py
    assert all(x.category == "python" for x in py)


def test_agent_frameworks_category():
    fw = get_by_category("agent_frameworks")
    assert len(fw) >= 100
    assert any("LangGraph" in x.question or "LangGraph" in x.answer for x in fw)
    assert any("n8n" in x.question.lower() or "n8n" in x.answer.lower() for x in fw)


def test_intermediate_agent_frameworks():
    items = get_by_difficulty("intermediate", category="agent_frameworks")
    assert len(items) >= 55
    assert all(x.difficulty == "intermediate" for x in items)
    assert any("LangGraph" in x.question for x in items)


def test_prompt_engineering_category():
    pe = get_by_category("prompt_engineering")
    assert len(pe) >= 100


def test_loop_engineering_category():
    lp = get_by_category("loop_engineering")
    assert len(lp) >= 100
