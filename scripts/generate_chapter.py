#!/usr/bin/env python3
"""Generate production-quality book chapters from the master authoring prompts.

Examples:
  python scripts/generate_chapter.py --chapter 1 --dry-run
  python scripts/generate_chapter.py --chapter 3 --force
  python scripts/generate_chapter.py --start 1 --end 5 --dry-run
  python scripts/generate_chapter.py --chapters 1,2,8-10
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel
from rich.table import Table

# Allow `python scripts/generate_chapter.py` without installing a package.
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.chapter import (  # noqa: E402
    ensure_chapter_header,
    update_chapter_status,
    validate_structure,
    write_chapter,
)
from lib.cli_common import bootstrap, echo_info, echo_success, echo_warn, parse_chapter_list, write_json  # noqa: E402
from lib.llm import LLMClient, LLMError, save_prompt_bundle  # noqa: E402
from lib.logging_utils import console, die  # noqa: E402
from lib.prompts import compose_chapter_system, compose_chapter_user  # noqa: E402

app = typer.Typer(
    add_completion=False,
    help="Generate book chapters using MASTER_BOOK_CREATION_PROMPT + source-of-truth docs.",
    no_args_is_help=True,
)


@app.command()
def main(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c", help="Single chapter number."),
    chapters: Optional[str] = typer.Option(
        None, "--chapters", help="Comma/range list, e.g. 1,2,5-8"
    ),
    start: Optional[int] = typer.Option(None, "--start", help="Start of chapter range."),
    end: Optional[int] = typer.Option(None, "--end", help="End of chapter range."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing chapter files."),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Build prompts only; do not call the LLM or write chapters."
    ),
    lookback: int = typer.Option(2, "--lookback", help="Prior chapters to include for continuity."),
    notes: str = typer.Option("", "--notes", help="Extra author instructions for the model."),
    provider: Optional[str] = typer.Option(None, "--provider", help="openai | anthropic | openai_compatible"),
    model: Optional[str] = typer.Option(None, "--model", help="Model name override."),
    config: Optional[Path] = typer.Option(None, "--config", help="Path to scripts/config.yaml"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    validate_only: bool = typer.Option(
        False, "--validate-only", help="Validate existing chapters; do not generate."
    ),
) -> None:
    """Generate one or more chapters into book/chapter-XXX.md."""
    paths, cfg, curriculum = bootstrap(
        verbose=verbose,
        dry_run=dry_run,
        config=config,
        provider=provider,
        model=model,
    )

    try:
        targets = parse_chapter_list(chapter, chapters, start, end, curriculum)
    except Exception as exc:  # noqa: BLE001
        die(str(exc))

    if validate_only:
        table = Table(title="Chapter Structure Validation")
        table.add_column("Ch")
        table.add_column("Title")
        table.add_column("OK")
        table.add_column("Missing")
        table.add_column("Words")
        for n in targets:
            path = paths.chapter_md(n)
            if not path.is_file():
                table.add_row(f"{n:03d}", "—", "NO", "file missing", "0")
                continue
            report = validate_structure(n, path.read_text(encoding="utf-8"), path)
            table.add_row(
                f"{n:03d}",
                report.title or "—",
                "YES" if report.structure_ok else "NO",
                ", ".join(report.missing_required[:4]) + ("…" if len(report.missing_required) > 4 else ""),
                str(report.word_count),
            )
        console.print(table)
        raise typer.Exit(0)

    client = LLMClient(cfg)
    system = compose_chapter_system(paths)
    results: list[dict] = []

    for n in targets:
        try:
            meta = curriculum.get(n)
        except KeyError as exc:
            die(str(exc))

        out_path = paths.chapter_md(n)
        console.print(
            Panel.fit(
                f"[bold]Chapter {n:03d}[/bold]: {meta.title}\n"
                f"Part: {meta.part or '—'} | Phase: {meta.phase or '—'}\n"
                f"Output: {paths.relative(out_path)}",
                title="Generate Chapter",
            )
        )

        if out_path.exists() and not force and not cfg.dry_run:
            echo_warn(f"Skipping {out_path.name} (exists). Use --force to overwrite.")
            results.append({"number": n, "status": "skipped_exists"})
            continue

        user = compose_chapter_user(
            paths,
            number=n,
            title=meta.title,
            part=meta.part,
            phase=meta.phase,
            objectives=meta.objectives,
            topics=meta.topics,
            notes=notes or meta.notes,
            lookback=lookback,
        )

        bundle_path = paths.state / "prompts" / f"generate-chapter-{n:03d}.json"
        save_prompt_bundle(
            bundle_path,
            system=system,
            user=user,
            meta={
                "chapter": n,
                "title": meta.title,
                "provider": cfg.llm.provider,
                "model": cfg.llm.model,
                "dry_run": cfg.dry_run,
            },
        )
        echo_info(f"Prompt bundle: {paths.relative(bundle_path)}")

        if cfg.dry_run:
            echo_success(f"Dry-run complete for chapter {n:03d} (no LLM call).")
            results.append({"number": n, "status": "dry_run", "prompt_bundle": str(bundle_path)})
            continue

        try:
            response = client.complete(system=system, user=user)
        except LLMError as exc:
            die(str(exc))

        content = ensure_chapter_header(meta, response.content)
        written = write_chapter(paths, n, content, force=True)
        structure = validate_structure(n, content, written)
        update_chapter_status(paths, n, "drafted", notes="generated by generate_chapter.py")

        report_path = paths.reports / f"chapter-{n:03d}-structure.json"
        write_json(report_path, structure.to_dict())

        if structure.missing_required:
            echo_warn(
                f"Chapter written but missing sections: {', '.join(structure.missing_required)}"
            )
        else:
            echo_success(f"Wrote {paths.relative(written)} ({structure.word_count} words)")

        results.append(
            {
                "number": n,
                "status": "written",
                "path": str(written),
                "structure_ok": structure.structure_ok,
                "missing_required": structure.missing_required,
                "usage": response.usage,
            }
        )

    summary_path = paths.reports / "generate_chapter_last_run.json"
    write_json(summary_path, {"results": results})
    echo_info(f"Run summary: {paths.relative(summary_path)}")


if __name__ == "__main__":
    app()
