import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pdfchat import PdfChat, InMemoryIndex, MockLLM, simple_chunk


def test_chunk():
    parts = simple_chunk("a " * 100, size=20, overlap=5)
    assert len(parts) >= 2


def test_retrieve_and_cite():
    app = PdfChat(index=InMemoryIndex(), llm=MockLLM())
    app.ingest("docA", "The capital of France is Paris. Paris is a city.")
    app.ingest("docB", "Python is a programming language used for agents.")
    r = app.ask("capital of France Paris")
    assert r["citations"]
    assert any("docA" in c for c in r["citations"])
    assert r["answer"].startswith("[grounded]")
