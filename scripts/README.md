# Authoring Automation Scripts

Production-grade workflow automation for **AI Agent Engineering Bootcamp (2026 Edition)**.

These scripts operationalize the master prompts and source-of-truth documents:

| Priority | Document |
|----------|----------|
| 1 | `BOOK_MANIFEST.md` |
| 2 | `BOOK_SPECIFICATION.md` |
| 3 | `BOOK_BIBLE.md` |
| 4 | `AI_ENGINEERING_PLAYBOOK.md` |

| Prompt | Used by |
|--------|---------|
| `prompts/MASTER_BOOK_CREATION_PROMPT.md` | `generate_chapter.py`, diagram generation |
| `prompts/MASTER_REVIEW_PROMPT.md` | `review_chapter.py` |
| `prompts/MASTER_CODE_GENERATION_PROMPT.md` | `generate_code.py` |
| `prompts/MASTER_PROJECT_MANAGER_PROMPT.md` | status/release planning conventions |

## Layout

```
scripts/
├── generate_chapter.py      # Draft chapters → book/chapter-XXX.md
├── review_chapter.py        # Structured editorial/technical reviews
├── generate_code.py         # Code packages → code/chapter-XXX/
├── generate_diagrams.py     # Mermaid sources → diagrams/mermaid/chapter-XXX/
├── build_book.py            # Assemble build/book.md (+ pandoc exports)
├── check_consistency.py     # Structure, continuity, quality gates
├── release.py               # Plan/package v0.1 … v1.0 releases
├── config.example.yaml
├── requirements.txt
├── data/curriculum.yaml     # All 94 chapters catalog
└── lib/                     # Shared production library
```

## Setup

```bash
cd AI-Agent-Engineering-Bootcamp
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements.txt

cp scripts/config.example.yaml scripts/config.yaml
export OPENAI_API_KEY=sk-...          # or ANTHROPIC_API_KEY
# optional overrides:
# export BOOK_LLM_PROVIDER=anthropic
# export BOOK_LLM_MODEL=claude-sonnet-4-20250514
```

## Recommended workflow

```bash
# 1) Generate a chapter (dry-run first — writes prompt bundles only)
python scripts/generate_chapter.py --chapter 1 --dry-run
python scripts/generate_chapter.py --chapter 1

# 2) Structural / consistency gate
python scripts/check_consistency.py --chapter 1

# 3) Human or LLM review
python scripts/review_chapter.py --chapter 1

# 4) Code package for the chapter
python scripts/generate_code.py --chapter 1

# 5) Diagrams (extract from markdown or regenerate)
python scripts/generate_diagrams.py --chapter 1 --extract-only
python scripts/generate_diagrams.py --chapter 1

# 6) Assemble book
python scripts/build_book.py --start 1 --end 10

# 7) Package a release milestone
python scripts/release.py plan --version v0.1
python scripts/release.py package --version v0.1
```

### Batch / CI-friendly patterns

```bash
# Multiple chapters
python scripts/generate_chapter.py --chapters 1,2,3 --dry-run
python scripts/generate_chapter.py --start 1 --end 5 --dry-run

# Progress dashboard
python scripts/check_consistency.py --progress

# Strict gate (fails on medium issues too)
python scripts/check_consistency.py --strict
echo $?   # 0 pass, 2 critical/high, 3 strict medium
```

## Outputs

| Path | Purpose |
|------|---------|
| `book/chapter-XXX.md` | Chapter drafts |
| `code/chapter-XXX/` | Code packages |
| `diagrams/mermaid/chapter-XXX/*.mmd` | Diagram sources |
| `reviews/chapter-XXX-review.md` | Review reports |
| `build/book.md` | Assembled manuscript |
| `releases/<version>-<timestamp>.zip` | Release archives |
| `reports/*.json` | Machine-readable run summaries |
| `.book_state/` | Prompt bundles, status DB, raw outputs |

## Script reference

### `generate_chapter.py`

Composes `MASTER_BOOK_CREATION_PROMPT` + source-of-truth docs + prior chapter continuity, then writes `book/chapter-XXX.md`.

Key flags: `--chapter`, `--chapters`, `--start/--end`, `--force`, `--dry-run`, `--lookback`, `--notes`, `--validate-only`, `--provider`, `--model`.

### `review_chapter.py`

Produces scorecard-style reviews (Accept / Minor / Major / Reject) into `reviews/`.

Key flags: `--focus full|technical|security|editorial|pedagogy|code`.

### `generate_code.py`

Generates multi-file Python under `code/chapter-XXX/` using path-fenced model output:

````markdown
```path:code/chapter-003/main.py
...
```
````

### `generate_diagrams.py`

- `--extract-only`: pull existing ```mermaid blocks from the chapter
- default: ask the model for improved architecture diagrams
- `--render`: optional PNG export via `@mermaid-js/mermaid-cli` (`mmdc`)

### `build_book.py`

Assembles existing chapters into `build/book.md` with TOC. Optional pandoc exports:

```bash
python scripts/build_book.py --formats md,html
```

### `check_consistency.py`

Checks:

- source-of-truth documents present
- required chapter sections (BOOK_SPECIFICATION template)
- hype/marketing language
- project continuity signals
- code package alignment

### `release.py`

Presets from the project manager prompt:

| Version | Label | Target |
|---------|-------|--------|
| v0.1 | First 10 Chapters | 1–10 |
| v0.5 | Half Complete | 1–47 |
| v0.9 | Technical Review | 1–90 |
| v1.0 | First Edition | 1–94 |

```bash
python scripts/release.py list-presets
python scripts/release.py status
python scripts/release.py package --version v0.1 --require-ready
```

## Design notes

- **Dry-run by default for cost control**: every generative script supports `--dry-run` and always writes audit prompt bundles under `.book_state/prompts/`.
- **Idempotent writes**: existing artifacts are skipped unless `--force`.
- **Exit codes**: consistency checks return non-zero for automation/CI gates.
- **Provider-agnostic LLM**: OpenAI, OpenAI-compatible base URLs, and Anthropic.
- **Curriculum catalog**: `scripts/data/curriculum.yaml` lists all 94 chapters with parts/phases.

## Safety

- Never commits secrets; uses env-based API keys only.
- Refuses path traversal when writing model-emitted files.
- Artifacts limited to `code/`, `diagrams/`, `book/`, `playbook/` prefixes.
