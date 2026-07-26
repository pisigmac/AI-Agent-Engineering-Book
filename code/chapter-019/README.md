# Chapter 019 — Chunking Strategies

Fixed, sliding, recursive, semantic, and hierarchical chunkers plus an ASCII chunk visualizer.

## Run

```bash
cd code/chapter-019
pip install pytest
pytest -q
python3 main.py visualize --strategy recursive
python3 main.py chunk --strategy semantic --format json --no-text
python3 main.py chunk --strategy hierarchical --size 220
python3 main.py compare --size 350
python3 main.py chunk --file ./README.md --strategy fixed --size 200
```

## Strategies

| Name | Idea |
|------|------|
| `fixed` | Equal char windows + overlap |
| `sliding` | Window + stride |
| `recursive` | Split on headings/paragraphs/sentences |
| `semantic` | Break on low adjacent sentence similarity |
| `hierarchical` | Parent sections + child passages |

## Layout

| Module | Role |
|--------|------|
| `fixed.py` / `sliding.py` | Window chunkers |
| `recursive.py` | Separator hierarchy |
| `semantic.py` | BOW cosine breakpoints |
| `hierarchical.py` | Parent/child graph |
| `visualize.py` | Terminal visualizer |
| `pipeline.py` | Registry + compare |
| `sample_docs.py` | Policy handbook fixture |
