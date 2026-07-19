#!/usr/bin/env python3
"""Validate structure, terminology, continuity, and artifact completeness.

Examples:
  python scripts/check_consistency.py
  python scripts/check_consistency.py --chapter 1
  python scripts/check_consistency.py --chapters 1-10 --strict
  python scripts/check_consistency.py --progress
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.table import Table

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.chapter import progress_report  # noqa: E402
from lib.cli_common import bootstrap, echo_info, echo_success, echo_warn, parse_chapter_list, write_json  # noqa: E402
from lib.consistency import render_report_markdown, run_consistency_checks  # noqa: E402
from lib.logging_utils import console, die  # noqa: E402

app = typer.Typer(
    add_completion=False,
    help="Consistency and quality gate for the bootcamp book repository.",
    no_args_is_help=False,
)


@app.command()
def main(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c"),
    chapters: Optional[str] = typer.Option(None, "--chapters"),
    start: Optional[int] = typer.Option(None, "--start"),
    end: Optional[int] = typer.Option(None, "--end"),
    all_written: bool = typer.Option(
        True,
        "--all-written/--no-all-written",
        help="When no chapter filter is set, check all written chapters.",
    ),
    progress: bool = typer.Option(False, "--progress", help="Show curriculum progress dashboard."),
    strict: bool = typer.Option(
        False, "--strict", help="Exit non-zero on medium issues as well as critical/high."
    ),
    config: Optional[Path] = typer.Option(None, "--config"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    write_report: bool = typer.Option(True, "--write-report/--no-write-report"),
) -> None:
    """Run consistency checks and emit reports under reports/."""
    paths, _cfg, curriculum = bootstrap(verbose=verbose, config=config)

    if progress:
        prog = progress_report(paths, curriculum)
        table = Table(title="Curriculum Progress")
        table.add_column("Metric")
        table.add_column("Value")
        table.add_row("Total chapters", str(prog["total_chapters"]))
        table.add_row("Files present", str(prog["files_present"]))
        table.add_row("Files missing", str(prog["files_missing"]))
        for status, count in (prog.get("status_counts") or {}).items():
            if count:
                table.add_row(f"Status: {status}", str(count))
        console.print(table)
        if prog["missing_chapter_numbers"]:
            preview = ", ".join(f"{n:03d}" for n in prog["missing_chapter_numbers"][:30])
            echo_info(f"Missing (sample): {preview}")
        write_json(paths.reports / "progress.json", prog)

    numbers: list[int] | None
    if chapter is not None or chapters or start is not None or end is not None:
        numbers = parse_chapter_list(chapter, chapters, start, end, curriculum)
    elif all_written:
        numbers = [c.number for c in curriculum if paths.chapter_md(c.number).is_file()]
    else:
        numbers = [c.number for c in curriculum]

    report = run_consistency_checks(paths, curriculum, numbers=numbers)
    md = render_report_markdown(report)
    console.print(md)

    if write_report:
        md_path = paths.reports / "consistency_report.md"
        json_path = paths.reports / "consistency_report.json"
        md_path.write_text(md, encoding="utf-8")
        write_json(json_path, report.to_dict())
        echo_info(f"Wrote {paths.relative(md_path)}")
        echo_info(f"Wrote {paths.relative(json_path)}")

    if report.summary.get("critical", 0) or report.summary.get("high", 0):
        echo_warn("Consistency gate FAILED (critical/high issues present).")
        raise typer.Exit(2)
    if strict and report.summary.get("medium", 0):
        echo_warn("Consistency gate FAILED under --strict (medium issues present).")
        raise typer.Exit(3)

    echo_success("Consistency gate PASSED.")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
