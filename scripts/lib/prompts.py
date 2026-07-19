"""Load master prompts and compose generation/review requests."""

from __future__ import annotations

from pathlib import Path

from .paths import RepoPaths

# Soft token budget for context packing (chars ≈ tokens * 4 rough heuristic)
_MAX_CONTEXT_CHARS = 180_000


def read_text(path: Path, *, max_chars: int | None = None) -> str:
    if not path.is_file():
        return f"[MISSING DOCUMENT: {path.name}]"
    text = path.read_text(encoding="utf-8")
    if max_chars is not None and len(text) > max_chars:
        half = max_chars // 2
        return (
            text[:half]
            + f"\n\n[... truncated {len(text) - max_chars} characters ...]\n\n"
            + text[-half:]
        )
    return text


def load_source_of_truth(paths: RepoPaths, *, budget: int = _MAX_CONTEXT_CHARS) -> str:
    """Load hierarchical source-of-truth documents within a rough budget."""
    # Priority weights — specification is large; keep more of higher-priority docs
    slices = [
        (paths.manifest, 8_000),
        (paths.bible, 40_000),
        (paths.playbook_doc, 30_000),
        (paths.specification, 100_000),
    ]
    parts: list[str] = []
    used = 0
    for path, allotment in slices:
        remaining = budget - used
        if remaining <= 0:
            break
        chunk = read_text(path, max_chars=min(allotment, remaining))
        parts.append(f"# SOURCE DOCUMENT: {path.name}\n\n{chunk}")
        used += len(chunk)
    return "\n\n---\n\n".join(parts)


def load_master_prompt(paths: RepoPaths, kind: str) -> str:
    mapping = {
        "book": paths.master_book,
        "review": paths.master_review,
        "code": paths.master_code,
        "pm": paths.master_pm,
    }
    if kind not in mapping:
        raise ValueError(f"Unknown prompt kind: {kind}. Expected one of {list(mapping)}")
    return read_text(mapping[kind])


def previous_chapters_context(
    paths: RepoPaths,
    chapter_number: int,
    *,
    lookback: int = 2,
    max_chars_each: int = 12_000,
) -> str:
    """Include summaries/excerpts of recent prior chapters for continuity."""
    parts: list[str] = []
    start = max(1, chapter_number - lookback)
    for n in range(start, chapter_number):
        path = paths.chapter_md(n)
        if not path.is_file():
            parts.append(f"## Chapter {n:03d}\n\n[Not yet written]")
            continue
        text = read_text(path, max_chars=max_chars_each)
        parts.append(f"## Prior Chapter File: {path.name}\n\n{text}")
    if not parts:
        return "[No prior chapters available — this is an early chapter.]"
    return "\n\n---\n\n".join(parts)


def compose_chapter_system(paths: RepoPaths) -> str:
    master = load_master_prompt(paths, "book")
    return (
        f"{master}\n\n"
        "You MUST follow the required chapter structure from BOOK_SPECIFICATION.md exactly.\n"
        "Output a complete chapter in Markdown only. Do not wrap the chapter in outer fences.\n"
        "Begin with a single H1 title. Include Mermaid diagrams where architecture is discussed.\n"
    )


def compose_chapter_user(
    paths: RepoPaths,
    *,
    number: int,
    title: str,
    part: str,
    phase: str,
    objectives: list[str],
    topics: list[str],
    notes: str = "",
    lookback: int = 2,
) -> str:
    sot = load_source_of_truth(paths)
    prior = previous_chapters_context(paths, number, lookback=lookback)
    obj_block = "\n".join(f"- {o}" for o in objectives) or "- (derive from BOOK_SPECIFICATION)"
    topic_block = "\n".join(f"- {t}" for t in topics) or "- (derive from BOOK_SPECIFICATION)"
    notes_block = notes.strip() or "(none)"
    return f"""# TASK: Generate Chapter {number:03d}

## Chapter Metadata
- Number: {number}
- Title: {title}
- Part: {part}
- Phase: {phase}
- Output path: book/chapter-{number:03d}.md
- Code path (if needed later): code/chapter-{number:03d}/
- Diagram path: diagrams/mermaid/chapter-{number:03d}/

## Learning Objectives
{obj_block}

## Topics / Focus
{topic_block}

## Author Notes
{notes_block}

## Continuity Rules
1. Build on the single evolving AI platform project.
2. Reuse canonical terminology from BOOK_BIBLE.md.
3. Never invent contradictory architecture.
4. Teach WHY → WHAT → HOW → IMPLEMENT → DEBUG → EVALUATE → DEPLOY.
5. Build manually before frameworks.
6. Include production concerns: security, performance, observability, evaluation.
7. Complete every required section from the chapter template.

## Prior Chapter Context
{prior}

## Source of Truth Documents
{sot}

Generate the full chapter now.
"""


def compose_review_system(paths: RepoPaths) -> str:
    master = load_master_prompt(paths, "review")
    return (
        f"{master}\n\n"
        "Return the review in the exact OUTPUT FORMAT specified.\n"
        "Do not rewrite the chapter unless the user prompt explicitly requests a rewrite.\n"
    )


def compose_review_user(
    paths: RepoPaths,
    *,
    number: int,
    chapter_text: str,
    focus: str = "full",
) -> str:
    sot = load_source_of_truth(paths, budget=80_000)
    return f"""# TASK: Review Chapter {number:03d}

## Review Focus
{focus}

## Chapter Under Review
Path: book/chapter-{number:03d}.md

{chapter_text}

## Source of Truth (for consistency checks)
{sot}

Produce a structured review now.
"""


def compose_code_system(paths: RepoPaths) -> str:
    master = load_master_prompt(paths, "code")
    return (
        f"{master}\n\n"
        "Output production-quality Python for the requested chapter.\n"
        "Prefer a multi-file layout. When emitting files, use this exact format:\n\n"
        "```path:relative/path/from/repo/root.py\n"
        "# file contents\n"
        "```\n\n"
        "Also include tests under the chapter code directory.\n"
        "Do not invent a conflicting project structure.\n"
    )


def compose_code_user(
    paths: RepoPaths,
    *,
    number: int,
    title: str,
    chapter_excerpt: str,
    instructions: str = "",
) -> str:
    sot = load_source_of_truth(paths, budget=60_000)
    extra = instructions.strip() or "Generate the code artifacts implied by this chapter."
    return f"""# TASK: Generate Code for Chapter {number:03d} — {title}

## Output Directory
code/chapter-{number:03d}/

## Instructions
{extra}

## Chapter Excerpt
{chapter_excerpt}

## Source of Truth
{sot}

Generate the code package now.
"""


def compose_diagram_system(paths: RepoPaths) -> str:
    master = load_master_prompt(paths, "book")
    return (
        "You are a principal software architect specializing in technical diagrams.\n"
        "Extract and produce Mermaid diagrams for the given chapter.\n"
        "Follow diagram standards from BOOK_SPECIFICATION.md and BOOK_BIBLE.md.\n"
        "Output ONLY Mermaid fenced blocks. For each diagram, use this format:\n\n"
        "### Diagram: <short-slug>\n"
        "```mermaid\n"
        "...\n"
        "```\n\n"
        f"Master context excerpt:\n{master[:4000]}\n"
    )


def compose_diagram_user(paths: RepoPaths, *, number: int, chapter_text: str) -> str:
    return f"""# TASK: Generate / Extract Architecture Diagrams for Chapter {number:03d}

## Chapter Content
{chapter_text[:80_000]}

## Requirements
- Produce 1–5 Mermaid diagrams that clarify architecture, sequence, state, or class structure.
- Prefer correctness over decoration.
- Align with the book's canonical architecture layers and terminology.
- If the chapter already contains Mermaid blocks, refine and improve them; still emit complete blocks.

Generate diagrams now.
"""
