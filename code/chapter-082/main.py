#!/usr/bin/env python3
import json
from pdfchat import PdfChat, InMemoryIndex, MockLLM


def main() -> int:
    app = PdfChat(index=InMemoryIndex(), llm=MockLLM())
    app.ingest("handbook", "Agent memory stores conversation state. Vector indexes speed retrieval.")
    app.ingest("handbook", "Evaluation uses golden datasets and scorers for quality gates.", page=2)
    r = app.ask("How does agent memory work?")
    print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
