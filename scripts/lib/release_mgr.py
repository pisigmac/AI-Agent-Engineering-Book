"""Release packaging and version management."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .chapter import progress_report
from .curriculum import Curriculum
from .paths import RepoPaths

PRESET_RELEASES = {
    "v0.1": {"label": "First 10 Chapters", "max_chapter": 10},
    "v0.5": {"label": "Half Complete", "max_chapter": 47},
    "v0.9": {"label": "Technical Review", "max_chapter": 90},
    "v1.0": {"label": "First Edition", "max_chapter": 95},
    "v1.1": {"label": "Errata", "max_chapter": 95},
    "v2.0": {"label": "New Framework Updates", "max_chapter": 95},
}


@dataclass
class ReleasePlan:
    version: str
    label: str
    max_chapter: int
    chapters_ready: list[int] = field(default_factory=list)
    chapters_missing: list[int] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def readiness_pct(self) -> float:
        total = self.max_chapter
        if total <= 0:
            return 0.0
        return 100.0 * len(self.chapters_ready) / total


def plan_release(
    paths: RepoPaths,
    curriculum: Curriculum,
    version: str,
    *,
    max_chapter: int | None = None,
    label: str | None = None,
) -> ReleasePlan:
    preset = PRESET_RELEASES.get(version, {})
    max_ch = max_chapter or int(preset.get("max_chapter") or 95)
    lab = label or str(preset.get("label") or version)

    ready: list[int] = []
    missing: list[int] = []
    for n in range(1, max_ch + 1):
        if paths.chapter_md(n).is_file():
            ready.append(n)
        else:
            missing.append(n)

    return ReleasePlan(
        version=version,
        label=lab,
        max_chapter=max_ch,
        chapters_ready=ready,
        chapters_missing=missing,
    )


def _git_info(root: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"available": False}
    if not shutil.which("git"):
        return info
    try:
        def run(args: list[str]) -> str:
            return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

        info["available"] = True
        info["commit"] = run(["rev-parse", "HEAD"])
        info["branch"] = run(["rev-parse", "--abbrev-ref", "HEAD"])
        info["dirty"] = bool(run(["status", "--porcelain"]))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return info


def create_release_package(
    paths: RepoPaths,
    curriculum: Curriculum,
    plan: ReleasePlan,
    *,
    include_code: bool = True,
    include_diagrams: bool = True,
    include_build: bool = True,
) -> Path:
    paths.releases.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    release_dir = paths.releases / f"{plan.version}-{stamp}"
    release_dir.mkdir(parents=True, exist_ok=False)

    # Copy chapters
    book_out = release_dir / "book"
    book_out.mkdir()
    for n in plan.chapters_ready:
        src = paths.chapter_md(n)
        shutil.copy2(src, book_out / src.name)

    if include_code:
        code_out = release_dir / "code"
        code_out.mkdir()
        for n in plan.chapters_ready:
            src = paths.chapter_code_dir(n)
            if src.is_dir():
                shutil.copytree(src, code_out / src.name)

    if include_diagrams:
        diag_out = release_dir / "diagrams"
        for n in plan.chapters_ready:
            src = paths.chapter_diagram_dir(n)
            if src.is_dir():
                dest = diag_out / "mermaid" / src.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(src, dest)

    if include_build:
        build_md = paths.build / "book.md"
        if build_md.is_file():
            (release_dir / "build").mkdir(exist_ok=True)
            shutil.copy2(build_md, release_dir / "build" / "book.md")

    # Core docs
    for doc in (
        paths.manifest,
        paths.specification,
        paths.bible,
        paths.playbook_doc,
    ):
        if doc.is_file():
            shutil.copy2(doc, release_dir / doc.name)

    progress = progress_report(paths, curriculum)
    metadata = {
        "version": plan.version,
        "label": plan.label,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "max_chapter": plan.max_chapter,
        "chapters_ready": plan.chapters_ready,
        "chapters_missing": plan.chapters_missing,
        "readiness_pct": plan.readiness_pct,
        "progress": progress,
        "git": _git_info(paths.root),
    }
    (release_dir / "RELEASE.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    notes = f"""# Release {plan.version} — {plan.label}

Generated: {metadata['created_at']}

## Readiness

- Target chapters: 1–{plan.max_chapter}
- Ready: {len(plan.chapters_ready)}
- Missing: {len(plan.chapters_missing)}
- Readiness: {plan.readiness_pct:.1f}%

## Missing Chapters

{', '.join(f'{n:03d}' for n in plan.chapters_missing) or '_None_'}

## Git

```json
{json.dumps(metadata['git'], indent=2)}
```
"""
    (release_dir / "RELEASE_NOTES.md").write_text(notes, encoding="utf-8")

    # Zip archive
    archive_base = paths.releases / f"{plan.version}-{stamp}"
    archive = shutil.make_archive(str(archive_base), "zip", root_dir=release_dir)
    return Path(archive)
