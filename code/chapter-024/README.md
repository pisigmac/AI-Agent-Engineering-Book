# Chapter 024 — Production RAG

End-to-end RAG: retriever → ranker → prompt assembly (untrusted evidence) → citations → memory → grounded generator.

## Run

```bash
cd code/chapter-024
pip install pytest
pytest -q
python3 main.py ask "How do I get my money back?"
python3 main.py ask "HTTP 429" --where '{"topic":"developers"}'
python3 main.py chat
python3 main.py retrieve "password reset"
python3 main.py eval
```

## Pipeline

```text
question → retrieve(k) → rank → assemble prompt + citations
        → generate grounded answer → update memory
```

## Layout

| Module | Role |
|--------|------|
| `retriever.py` | Dense retrieve + filters |
| `ranker.py` | Lexical blend + topic boosts |
| `prompt.py` | System + memory + UNTRUSTED evidence |
| `citations.py` | [n] markers + footer |
| `memory.py` | Short-term turn buffer |
| `generator.py` | Extractive grounded mock LLM |
| `pipeline.py` | `RAGSystem.ask` |
| `eval.py` | Citation hit-rate harness |
