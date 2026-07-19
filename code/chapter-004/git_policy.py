"""Shared Git workflow policy for the AI platform monorepo."""

from __future__ import annotations

import re
from dataclasses import dataclass

CONVENTIONAL_TYPES = (
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
)

COMMIT_RE = re.compile(
    r"^(?P<type>"
    + "|".join(CONVENTIONAL_TYPES)
    + r")"
    r"(?:\((?P<scope>[a-z0-9/_.,-]+)\))?"
    r"(?P<breaking>!)?"
    r": "
    r"(?P<subject>.+)$"
)

BRANCH_RE = re.compile(
    r"^(main|master|develop)$|"
    r"^(feat|fix|docs|chore|test|refactor|ci|perf|release)/[a-z0-9._/-]+$"
)

AREA_PREFIXES: dict[str, tuple[str, ...]] = {
    "book": ("book/",),
    "code": ("code/",),
    "diagrams": ("diagrams/",),
    "scripts": ("scripts/",),
    "source_of_truth": (
        "BOOK_MANIFEST.md",
        "BOOK_SPECIFICATION.md",
        "BOOK_BIBLE.md",
        "AI_ENGINEERING_PLAYBOOK.md",
    ),
}


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
