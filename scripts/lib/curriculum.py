"""Curriculum catalog: chapter metadata, parts, and phases."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

import yaml

from .paths import RepoPaths

# Required H2 sections from BOOK_SPECIFICATION chapter template.
# Aliases allow minor wording differences across prompts.
REQUIRED_SECTIONS: list[tuple[str, tuple[str, ...]]] = [
    ("Chapter Overview", ("Chapter Overview", "Overview")),
    ("Learning Objectives", ("Learning Objectives",)),
    ("Prerequisites", ("Prerequisites",)),
    ("Motivation", ("Motivation",)),
    ("First Principles", ("First Principles",)),
    ("Mental Model", ("Mental Model",)),
    ("Core Theory", ("Core Theory",)),
    ("Architecture", ("Architecture",)),
    (
        "Internal Implementation",
        ("Internal Implementation", "Manual Implementation", "Implementation"),
    ),
    ("Production Implementation", ("Production Implementation",)),
    ("Trade-offs", ("Trade-offs", "Tradeoffs")),
    ("Debugging", ("Debugging",)),
    ("Performance", ("Performance",)),
    ("Security", ("Security",)),
    ("Best Practices", ("Best Practices",)),
    ("Anti-Patterns", ("Anti-Patterns", "Anti Patterns", "Antipatterns")),
    ("Hands-on Exercise", ("Hands-on Exercise", "Hands-On Exercise", "Exercise")),
    ("Mini Project", ("Mini Project",)),
    (
        "Chapter Deliverables",
        ("Chapter Deliverables", "Deliverables"),
    ),
    ("Interview Questions", ("Interview Questions",)),
    ("Quiz", ("Quiz",)),
    ("Cheat Sheet", ("Cheat Sheet", "Cheatsheet")),
    (
        "Curated Free Resources",
        ("Curated Free Resources", "Free Resources", "Resources"),
    ),
    ("Chapter Summary", ("Chapter Summary", "Summary")),
    ("What's Next", ("What's Next", "What Next", "Next Steps")),
]

OPTIONAL_SECTIONS: list[tuple[str, tuple[str, ...]]] = [
    (
        "Framework Implementation",
        ("Framework Implementation", "Framework Comparison", "Frameworks"),
    ),
]


@dataclass
class ChapterMeta:
    number: int
    title: str
    part: str = ""
    phase: str = ""
    objectives: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    notes: str = ""

    @property
    def slug(self) -> str:
        return f"chapter-{self.number:03d}"

    @property
    def filename(self) -> str:
        return f"{self.slug}.md"

    def to_dict(self) -> dict[str, Any]:
        return {
            "number": self.number,
            "title": self.title,
            "part": self.part,
            "phase": self.phase,
            "objectives": list(self.objectives),
            "topics": list(self.topics),
            "frameworks": list(self.frameworks),
            "notes": self.notes,
        }


class Curriculum:
    """In-memory curriculum loaded from YAML."""

    def __init__(self, chapters: dict[int, ChapterMeta], meta: dict[str, Any] | None = None) -> None:
        self.chapters = chapters
        self.meta = meta or {}

    def __len__(self) -> int:
        return len(self.chapters)

    def __iter__(self) -> Iterator[ChapterMeta]:
        for n in sorted(self.chapters):
            yield self.chapters[n]

    def get(self, number: int) -> ChapterMeta:
        if number not in self.chapters:
            raise KeyError(f"Chapter {number} is not in the curriculum catalog.")
        return self.chapters[number]

    def range(self, start: int, end: int) -> list[ChapterMeta]:
        return [self.get(n) for n in range(start, end + 1) if n in self.chapters]

    @classmethod
    def load(cls, path: Path | None = None, paths: RepoPaths | None = None) -> "Curriculum":
        paths = paths or RepoPaths()
        catalog_path = path or paths.curriculum_file
        if not catalog_path.is_file():
            raise FileNotFoundError(
                f"Curriculum catalog not found: {catalog_path}. "
                "Expected scripts/data/curriculum.yaml"
            )
        with catalog_path.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        chapters: dict[int, ChapterMeta] = {}
        for item in raw.get("chapters") or []:
            number = int(item["number"])
            chapters[number] = ChapterMeta(
                number=number,
                title=str(item["title"]),
                part=str(item.get("part") or ""),
                phase=str(item.get("phase") or ""),
                objectives=list(item.get("objectives") or []),
                topics=list(item.get("topics") or []),
                frameworks=list(item.get("frameworks") or []),
                notes=str(item.get("notes") or ""),
            )
        return cls(chapters=chapters, meta=raw.get("meta") or {})


def parse_heading_titles(markdown: str) -> list[str]:
    """Return H2 heading titles from markdown."""
    titles: list[str] = []
    for line in markdown.splitlines():
        if line.startswith("## ") and not line.startswith("###"):
            titles.append(line[3:].strip())
    return titles


def find_section_match(headings: list[str], aliases: tuple[str, ...]) -> str | None:
    lowered = {h.lower(): h for h in headings}
    for alias in aliases:
        if alias.lower() in lowered:
            return lowered[alias.lower()]
    # fuzzy contains
    for alias in aliases:
        for h in headings:
            if alias.lower() in h.lower():
                return h
    return None
