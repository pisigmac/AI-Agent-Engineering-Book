"""Shared Typer helpers for all authoring scripts."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .config import Config, load_config
from .curriculum import Curriculum
from .logging_utils import setup_logging
from .paths import RepoPaths, find_repo_root

console = Console()


def bootstrap(
    *,
    verbose: bool = False,
    dry_run: bool = False,
    config: Optional[Path] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[RepoPaths, Config, Curriculum]:
    """Initialize paths, config, logging, and curriculum."""
    # Ensure imports work when invoked as python scripts/foo.py
    scripts_dir = Path(__file__).resolve().parents[1]
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    root = find_repo_root()
    paths = RepoPaths(root)
    paths.ensure_layout()
    cfg = load_config(
        config,
        dry_run=dry_run,
        verbose=verbose,
        provider=provider,
        model=model,
    )
    setup_logging(verbose=cfg.verbose)
    curriculum = Curriculum.load(paths=paths)
    return paths, cfg, curriculum


def parse_chapter_list(
    chapter: Optional[int],
    chapters: Optional[str],
    start: Optional[int],
    end: Optional[int],
    curriculum: Curriculum,
) -> list[int]:
    """Resolve chapter selection from CLI options."""
    if chapter is not None:
        return [chapter]
    if chapters:
        nums: list[int] = []
        for part in chapters.split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                nums.extend(range(int(a), int(b) + 1))
            else:
                nums.append(int(part))
        return sorted(set(nums))
    if start is not None or end is not None:
        s = start or 1
        e = end or max(curriculum.chapters)
        return list(range(s, e + 1))
    raise typer.BadParameter("Specify --chapter, --chapters, or --start/--end")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def echo_success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


def echo_warn(message: str) -> None:
    console.print(f"[bold yellow]![/bold yellow] {message}")


def echo_info(message: str) -> None:
    console.print(f"[bold blue]→[/bold blue] {message}")
