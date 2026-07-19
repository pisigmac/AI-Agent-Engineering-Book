"""Chapter file IO, structure validation, and status tracking."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .curriculum import (
    OPTIONAL_SECTIONS,
    REQUIRED_SECTIONS,
    ChapterMeta,
    Curriculum,
    find_section_match,
    parse_heading_titles,
)
from .paths import RepoPaths

CHAPTER_STATUSES = [
    "planned",
    "outlined",
    "drafted",
    "reviewed",
    "code_complete",
    "diagrams_complete",
    "exercises_complete",
    "quiz_complete",
    "cheat_sheet_complete",
    "resources_added",
    "final_review",
    "published",
]


@dataclass
class StructureReport:
    number: int
    path: str
    exists: bool
    title: str | None
    missing_required: list[str] = field(default_factory=list)
    present_optional: list[str] = field(default_factory=list)
    heading_count: int = 0
    mermaid_count: int = 0
    word_count: int = 0
    has_quiz: bool = False
    has_interview: bool = False
    issues: list[str] = field(default_factory=list)

    @property
    def structure_ok(self) -> bool:
        return self.exists and not self.missing_required and not self.issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ChapterStatus:
    number: int
    status: str = "planned"
    updated_at: str = ""
    notes: str = ""
    artifacts: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def strip_code_fences(text: str) -> str:
    """If the model wrapped the whole chapter in a single fence, unwrap it."""
    stripped = text.strip()
    match = re.match(r"^```(?:markdown|md)?\s*\n(.*)\n```\s*$", stripped, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip() + "\n"
    return text if text.endswith("\n") else text + "\n"


def extract_title(markdown: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith("# ") and not line.startswith("##"):
            return line[2:].strip()
    return None


def count_mermaid(markdown: str) -> int:
    return len(re.findall(r"```mermaid\b", markdown, flags=re.IGNORECASE))


def word_count(markdown: str) -> int:
    # Rough count excluding fenced code
    without_code = re.sub(r"```.*?```", " ", markdown, flags=re.DOTALL)
    return len(re.findall(r"\b\w+\b", without_code))


def validate_structure(number: int, markdown: str, path: Path | None = None) -> StructureReport:
    headings = parse_heading_titles(markdown)
    missing: list[str] = []
    for canonical, aliases in REQUIRED_SECTIONS:
        if not find_section_match(headings, aliases):
            missing.append(canonical)

    present_optional: list[str] = []
    for canonical, aliases in OPTIONAL_SECTIONS:
        if find_section_match(headings, aliases):
            present_optional.append(canonical)

    issues: list[str] = []
    title = extract_title(markdown)
    if not title:
        issues.append("Missing H1 chapter title")
    if word_count(markdown) < 800:
        issues.append("Chapter appears too short (< 800 words)")
    if count_mermaid(markdown) == 0:
        # Soft issue for architecture-heavy chapters
        issues.append("No Mermaid diagrams found (expected for most chapters)")

    return StructureReport(
        number=number,
        path=str(path) if path else f"book/chapter-{number:03d}.md",
        exists=True,
        title=title,
        missing_required=missing,
        present_optional=present_optional,
        heading_count=len(headings),
        mermaid_count=count_mermaid(markdown),
        word_count=word_count(markdown),
        has_quiz=bool(find_section_match(headings, ("Quiz",))),
        has_interview=bool(find_section_match(headings, ("Interview Questions",))),
        issues=issues,
    )


def load_chapter(paths: RepoPaths, number: int) -> tuple[Path, str]:
    path = paths.chapter_md(number)
    if not path.is_file():
        raise FileNotFoundError(f"Chapter file not found: {path}")
    return path, path.read_text(encoding="utf-8")


def write_chapter(paths: RepoPaths, number: int, content: str, *, force: bool = False) -> Path:
    paths.book.mkdir(parents=True, exist_ok=True)
    path = paths.chapter_md(number)
    if path.exists() and not force:
        raise FileExistsError(
            f"{path} already exists. Pass --force to overwrite."
        )
    cleaned = strip_code_fences(content)
    path.write_text(cleaned, encoding="utf-8")
    return path


def chapter_artifact_map(paths: RepoPaths, number: int) -> dict[str, bool]:
    code_dir = paths.chapter_code_dir(number)
    diagram_dir = paths.chapter_diagram_dir(number)
    chapter_path = paths.chapter_md(number)
    has_inline_mermaid = False
    if chapter_path.is_file():
        has_inline_mermaid = count_mermaid(chapter_path.read_text(encoding="utf-8")) > 0
    has_diagram_files = diagram_dir.is_dir() and any(diagram_dir.glob("*.mmd"))
    return {
        "chapter_md": chapter_path.is_file(),
        "review": paths.chapter_review(number).is_file(),
        "code_dir": code_dir.is_dir() and any(code_dir.rglob("*")),
        "tests": code_dir.is_dir() and any(code_dir.rglob("test_*.py")),
        "readme": code_dir.is_dir() and (code_dir / "README.md").is_file(),
        "diagrams": bool(has_diagram_files or has_inline_mermaid),
    }


def load_status_db(paths: RepoPaths) -> dict[str, Any]:
    path = paths.state / "chapter_status.json"
    if not path.is_file():
        return {"chapters": {}, "updated_at": None}
    return json.loads(path.read_text(encoding="utf-8"))


def save_status_db(paths: RepoPaths, db: dict[str, Any]) -> Path:
    paths.state.mkdir(parents=True, exist_ok=True)
    path = paths.state / "chapter_status.json"
    db["updated_at"] = now_iso()
    path.write_text(json.dumps(db, indent=2) + "\n", encoding="utf-8")
    return path


def update_chapter_status(
    paths: RepoPaths,
    number: int,
    status: str,
    *,
    notes: str = "",
) -> ChapterStatus:
    if status not in CHAPTER_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Expected one of {CHAPTER_STATUSES}")
    db = load_status_db(paths)
    entry = ChapterStatus(
        number=number,
        status=status,
        updated_at=now_iso(),
        notes=notes,
        artifacts=chapter_artifact_map(paths, number),
    )
    db.setdefault("chapters", {})[str(number)] = entry.to_dict()
    save_status_db(paths, db)
    return entry


def progress_report(paths: RepoPaths, curriculum: Curriculum) -> dict[str, Any]:
    db = load_status_db(paths)
    statuses = db.get("chapters") or {}
    by_status: dict[str, int] = {s: 0 for s in CHAPTER_STATUSES}
    missing_files: list[int] = []
    drafted: list[int] = []
    for ch in curriculum:
        path = paths.chapter_md(ch.number)
        if not path.is_file():
            missing_files.append(ch.number)
        else:
            drafted.append(ch.number)
        st = (statuses.get(str(ch.number)) or {}).get("status", "planned")
        if st not in by_status:
            by_status[st] = 0
        by_status[st] = by_status.get(st, 0) + 1

    return {
        "total_chapters": len(curriculum),
        "files_present": len(drafted),
        "files_missing": len(missing_files),
        "missing_chapter_numbers": missing_files,
        "status_counts": by_status,
        "updated_at": db.get("updated_at"),
    }


def ensure_chapter_header(meta: ChapterMeta, content: str) -> str:
    """If model omitted H1, prepend a standard title."""
    if extract_title(content):
        return content
    header = f"# Chapter {meta.number}: {meta.title}\n\n"
    return header + content.lstrip()
