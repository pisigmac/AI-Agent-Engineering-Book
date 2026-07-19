"""Assemble and optionally convert the full book from chapter files."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .curriculum import Curriculum
from .paths import RepoPaths


@dataclass
class BuildResult:
    success: bool
    markdown_path: Path | None
    epub_path: Path | None = None
    pdf_path: Path | None = None
    html_path: Path | None = None
    chapters_included: list[int] | None = None
    missing_chapters: list[int] | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "markdown_path": str(self.markdown_path) if self.markdown_path else None,
            "epub_path": str(self.epub_path) if self.epub_path else None,
            "pdf_path": str(self.pdf_path) if self.pdf_path else None,
            "html_path": str(self.html_path) if self.html_path else None,
            "chapters_included": self.chapters_included or [],
            "missing_chapters": self.missing_chapters or [],
            "message": self.message,
        }


def _front_matter(paths: RepoPaths, curriculum: Curriculum) -> str:
    title = "AI Agent Engineering Bootcamp (2026 Edition)"
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return f"""---
title: "{title}"
subtitle: "From Python to Production AI Agent Systems"
generated: "{generated}"
---

# {title}

**From Python to Production AI Agent Systems**

> Engineering textbook · Production handbook · Project-based curriculum

---

## About This Book

This book teaches AI systems engineering from first principles.
Frameworks are examples. Engineering principles are the subject.

See `BOOK_MANIFEST.md` and `BOOK_SPECIFICATION.md` for the canonical rules.

---

## Table of Contents

"""


def build_toc(curriculum: Curriculum, included: set[int]) -> str:
    lines: list[str] = []
    current_part = None
    for ch in curriculum:
        if ch.part and ch.part != current_part:
            current_part = ch.part
            lines.append(f"\n### {current_part}\n")
        marker = "✓" if ch.number in included else "○"
        lines.append(f"- {marker} Chapter {ch.number:02d}. {ch.title}")
    lines.append("\n---\n")
    return "\n".join(lines)


def assemble_markdown(
    paths: RepoPaths,
    curriculum: Curriculum,
    *,
    start: int = 1,
    end: int | None = None,
    only_existing: bool = True,
) -> BuildResult:
    paths.build.mkdir(parents=True, exist_ok=True)
    end = end or max((c.number for c in curriculum), default=94)
    included: list[int] = []
    missing: list[int] = []
    body_parts: list[str] = []

    for ch in curriculum:
        if ch.number < start or ch.number > end:
            continue
        path = paths.chapter_md(ch.number)
        if not path.is_file():
            missing.append(ch.number)
            if only_existing:
                continue
            body_parts.append(
                f"# Chapter {ch.number}: {ch.title}\n\n"
                f"_This chapter has not been written yet._\n\n---\n"
            )
            continue
        text = path.read_text(encoding="utf-8").strip() + "\n"
        included.append(ch.number)
        body_parts.append(text)
        body_parts.append("\n\\newpage\n\n")

    if not included and only_existing:
        return BuildResult(
            success=False,
            markdown_path=None,
            chapters_included=[],
            missing_chapters=missing,
            message="No chapter files found to assemble.",
        )

    md_path = paths.build / "book.md"
    content = (
        _front_matter(paths, curriculum)
        + build_toc(curriculum, set(included))
        + "\n\n".join(body_parts)
    )
    md_path.write_text(content, encoding="utf-8")

    # Manifest of build
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "chapters_included": included,
        "missing_chapters": missing,
        "output": str(md_path),
    }
    (paths.build / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    return BuildResult(
        success=True,
        markdown_path=md_path,
        chapters_included=included,
        missing_chapters=missing,
        message=f"Assembled {len(included)} chapters into {md_path}",
    )


def _run_pandoc(args: list[str]) -> None:
    if not shutil.which("pandoc"):
        raise RuntimeError("pandoc is not installed or not on PATH")
    subprocess.run(args, check=True, capture_output=True, text=True)


def convert_formats(
    markdown_path: Path,
    build_dir: Path,
    *,
    formats: list[str],
) -> dict[str, Path | None]:
    outputs: dict[str, Path | None] = {fmt: None for fmt in formats}
    for fmt in formats:
        if fmt == "md":
            outputs["md"] = markdown_path
            continue
        out = build_dir / f"book.{fmt}"
        if fmt == "html":
            _run_pandoc(
                [
                    "pandoc",
                    str(markdown_path),
                    "-o",
                    str(out),
                    "--standalone",
                    "--toc",
                    "--from",
                    "markdown",
                    "--to",
                    "html5",
                ]
            )
        elif fmt == "epub":
            _run_pandoc(
                [
                    "pandoc",
                    str(markdown_path),
                    "-o",
                    str(out),
                    "--toc",
                    "--from",
                    "markdown",
                ]
            )
        elif fmt == "pdf":
            _run_pandoc(
                [
                    "pandoc",
                    str(markdown_path),
                    "-o",
                    str(out),
                    "--toc",
                    "--from",
                    "markdown",
                    "-V",
                    "geometry:margin=1in",
                ]
            )
        else:
            raise ValueError(f"Unsupported format: {fmt}")
        outputs[fmt] = out
    return outputs
