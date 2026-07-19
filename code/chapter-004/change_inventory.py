"""Map changed paths to monorepo areas and chapters."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass

from git_policy import AREA_PREFIXES

CHAPTER_RE = re.compile(r"chapter-(\d{3})")


@dataclass(frozen=True)
class ChangeInventory:
    areas: dict[str, list[str]]
    chapters: dict[str, list[str]]
    other: list[str]

    def summary_lines(self) -> list[str]:
        lines: list[str] = []
        for area in sorted(self.areas):
            lines.append(f"area:{area} ({len(self.areas[area])} files)")
        for ch in sorted(self.chapters):
            lines.append(f"chapter:{ch} ({len(self.chapters[ch])} files)")
        if self.other:
            lines.append(f"other: {len(self.other)} files")
        return lines


def inventory_paths(paths: list[str]) -> ChangeInventory:
    areas: dict[str, list[str]] = defaultdict(list)
    chapters: dict[str, list[str]] = defaultdict(list)
    other: list[str] = []

    for raw in paths:
        path = raw.strip().replace("\\", "/")
        if not path:
            continue
        matched_area = False
        for area, prefixes in AREA_PREFIXES.items():
            if any(path == p or path.startswith(p) for p in prefixes):
                areas[area].append(path)
                matched_area = True
                break
        ch = CHAPTER_RE.search(path)
        if ch:
            chapters[ch.group(1)].append(path)
        if not matched_area:
            other.append(path)

    return ChangeInventory(
        areas=dict(areas),
        chapters=dict(chapters),
        other=other,
    )
