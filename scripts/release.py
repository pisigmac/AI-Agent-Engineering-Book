#!/usr/bin/env python3
"""Plan and package book releases (v0.1 … v1.0) for the bootcamp project.

Examples:
  python scripts/release.py plan --version v0.1
  python scripts/release.py package --version v0.1
  python scripts/release.py package --version v0.5 --require-ready
  python scripts/release.py list-presets
  python scripts/release.py status
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
from lib.cli_common import bootstrap, echo_info, echo_success, echo_warn, write_json  # noqa: E402
from lib.logging_utils import console, die  # noqa: E402
from lib.markdown_book import assemble_markdown  # noqa: E402
from lib.release_mgr import PRESET_RELEASES, create_release_package, plan_release  # noqa: E402

app = typer.Typer(
    add_completion=False,
    help="Release planning and packaging for the AI Agent Engineering Bootcamp.",
    no_args_is_help=True,
)


@app.command("list-presets")
def list_presets() -> None:
    """Show predefined release milestones from the project manager prompt."""
    table = Table(title="Release Presets")
    table.add_column("Version")
    table.add_column("Label")
    table.add_column("Max Chapter")
    for version, meta in PRESET_RELEASES.items():
        table.add_row(version, str(meta["label"]), str(meta["max_chapter"]))
    console.print(table)


@app.command("status")
def status(
    config: Optional[Path] = typer.Option(None, "--config"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Show overall book progress and release readiness snapshot."""
    paths, _cfg, curriculum = bootstrap(verbose=verbose, config=config)
    prog = progress_report(paths, curriculum)
    table = Table(title="Release Readiness Snapshot")
    table.add_column("Metric")
    table.add_column("Value")
    table.add_row("Total chapters", str(prog["total_chapters"]))
    table.add_row("Written", str(prog["files_present"]))
    table.add_row("Missing", str(prog["files_missing"]))
    console.print(table)

    preset_table = Table(title="Preset Readiness")
    preset_table.add_column("Version")
    preset_table.add_column("Ready")
    preset_table.add_column("Missing")
    preset_table.add_column("%")
    for version in PRESET_RELEASES:
        plan = plan_release(paths, curriculum, version)
        preset_table.add_row(
            version,
            str(len(plan.chapters_ready)),
            str(len(plan.chapters_missing)),
            f"{plan.readiness_pct:.1f}%",
        )
    console.print(preset_table)
    write_json(paths.reports / "release_status.json", prog)


@app.command("plan")
def plan_cmd(
    version: str = typer.Option(..., "--version", "-V", help="e.g. v0.1, v0.5, v1.0"),
    max_chapter: Optional[int] = typer.Option(None, "--max-chapter"),
    label: Optional[str] = typer.Option(None, "--label"),
    config: Optional[Path] = typer.Option(None, "--config"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Print a release plan without packaging."""
    paths, _cfg, curriculum = bootstrap(verbose=verbose, config=config)
    plan = plan_release(paths, curriculum, version, max_chapter=max_chapter, label=label)

    table = Table(title=f"Release Plan {plan.version} — {plan.label}")
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Max chapter", str(plan.max_chapter))
    table.add_row("Ready", str(len(plan.chapters_ready)))
    table.add_row("Missing", str(len(plan.chapters_missing)))
    table.add_row("Readiness", f"{plan.readiness_pct:.1f}%")
    console.print(table)

    if plan.chapters_missing:
        echo_warn(
            "Missing: " + ", ".join(f"{n:03d}" for n in plan.chapters_missing[:40])
            + ("…" if len(plan.chapters_missing) > 40 else "")
        )
    else:
        echo_success("All target chapters are present.")

    write_json(paths.reports / f"release_plan_{plan.version}.json", plan.to_dict())


@app.command("package")
def package_cmd(
    version: str = typer.Option(..., "--version", "-V"),
    max_chapter: Optional[int] = typer.Option(None, "--max-chapter"),
    label: Optional[str] = typer.Option(None, "--label"),
    require_ready: bool = typer.Option(
        False,
        "--require-ready",
        help="Fail if any target chapter markdown is missing.",
    ),
    rebuild: bool = typer.Option(
        True, "--rebuild/--no-rebuild", help="Assemble build/book.md before packaging."
    ),
    include_code: bool = typer.Option(True, "--include-code/--no-include-code"),
    include_diagrams: bool = typer.Option(True, "--include-diagrams/--no-include-diagrams"),
    config: Optional[Path] = typer.Option(None, "--config"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Create a dated release directory + zip under releases/."""
    paths, _cfg, curriculum = bootstrap(verbose=verbose, config=config)
    plan = plan_release(paths, curriculum, version, max_chapter=max_chapter, label=label)

    if require_ready and plan.chapters_missing:
        die(
            f"Release {version} not ready: missing {len(plan.chapters_missing)} chapter(s). "
            "Re-run without --require-ready to package partial content."
        )

    if rebuild and plan.chapters_ready:
        echo_info("Assembling markdown book for release…")
        build = assemble_markdown(
            paths,
            curriculum,
            start=1,
            end=plan.max_chapter,
            only_existing=True,
        )
        if build.success:
            echo_success(build.message)
        else:
            echo_warn(build.message)

    archive = create_release_package(
        paths,
        curriculum,
        plan,
        include_code=include_code,
        include_diagrams=include_diagrams,
        include_build=True,
    )
    echo_success(f"Release package: {paths.relative(archive)}")
    write_json(
        paths.reports / f"release_package_{plan.version}.json",
        {"archive": str(archive), "plan": plan.to_dict()},
    )


if __name__ == "__main__":
    app()
