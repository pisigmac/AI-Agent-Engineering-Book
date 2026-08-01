import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research import ResearchAgent, MockSearch, MockLLM


def test_research_loop():
    search = MockSearch(corpus=[
        {"title": "A", "url": "1", "snippet": "vector databases store embeddings"},
        {"title": "B", "url": "2", "snippet": "risks of vector databases"},
    ])
    agent = ResearchAgent(search=search, llm=MockLLM())
    r = agent.run("vector databases")
    assert r.subquestions
    assert r.synthesis
    assert any(e["type"] == "done" for e in r.events)
