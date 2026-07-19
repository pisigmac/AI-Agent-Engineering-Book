#!/usr/bin/env python3
"""Assemble the full book from chapter markdown files and optional pandoc exports.

Examples:
  python scripts/build_book.py
  python scripts/build_book.py --start 1 --end 10
  python scripts/build_book.py --formats md,html
  python scripts/build_book.py --include-missing
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

from lib.cli_common import bootstrap, echo_info, echo_success, echo_warn, write_json  # noqa: E402
from lib.logging_utils import console, die  # noqa: E402
from lib.markdown_book import assemble_markdown, convert_formats  # noqa: E402

app = typer.Typer(
    add_completion=False,
    help="Build consolidated book artifacts under build/.",
    no_args_is_help=False,
)


@app.command()
def main(
    start: int = typer.Option(1, "--start", help="First chapter number to include."),
    end: Optional[int] = typer.Option(None, "--end", help="Last chapter number to include."),
    formats: str = typer.Option(
        "md",
        "--formats",
        help="Comma-separated: md,html,epub,pdf (html/epub/pdf require pandoc).",
    ),
    include_missing: bool = typer.Option(
        False,
        "--include-missing",
        help="Insert placeholders for chapters that are not written yet.",
    ),
    config: Optional[Path] = typer.Option(None, "--config"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Assemble book/chapter-*.md into build/book.md and optional export formats."""
    paths, _cfg, curriculum = bootstrap(verbose=verbose, config=config)

    result = assemble_markdown(
        paths,
        curriculum,
        start=start,
        end=end,
        only_existing=not include_missing,
    )
    if not result.success:
        die(result.message)

    echo_success(result.message)

    table = Table(title="Build Summary")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Chapters included", str(len(result.chapters_included or [])))
    table.add_row("Chapters missing", str(len(result.missing_chapters or [])))
    table.add_row("Markdown output", paths.relative(result.markdown_path) if result.markdown_path else "—")
    console.print(table)

    if result.missing_chapters:
        preview = ", ".join(f"{n:03d}" for n in (result.missing_chapters or [])[:20])
        more = "" if len(result.missing_chapters or []) <= 20 else "…"
        echo_warn(f"Missing chapters: {preview}{more}")

    fmt_list = [f.strip().lower() for f in formats.split(",") if f.strip()]
    outputs = {"md": result.markdown_path}
    export_fmts = [f for f in fmt_list if f != "md"]
    if export_fmts:
        try:
            converted = convert_formats(result.markdown_path, paths.build, formats=export_fmts)
            outputs.update(converted)
            for fmt, path in converted.items():
                if path:
                    echo_success(f"Wrote {paths.relative(path)}")
        except Exception as exc:  # noqa: BLE001
            echo_warn(f"Format conversion failed: {exc}")
            echo_info("Install pandoc for html/epub/pdf export, or use --formats md")

    write_json(
        paths.reports / "build_book_last_run.json",
        {
            **result.to_dict(),
            "formats": fmt_list,
            "outputs": {k: str(v) if v else None for k, v in outputs.items()},
        },
    )


if __name__ == "__main__":
    app()
