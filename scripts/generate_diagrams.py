#!/usr/bin/env python3
"""Extract or generate Mermaid diagrams for chapters.

Examples:
  python scripts/generate_diagrams.py --chapter 2 --extract-only
  python scripts/generate_diagrams.py --chapter 28
  python scripts/generate_diagrams.py --chapters 27-30 --dry-run
  python scripts/generate_diagrams.py --chapter 2 --render  # requires mmdc
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.artifacts import extract_mermaid_blocks, write_mermaid_diagrams  # noqa: E402
from lib.chapter import load_chapter, update_chapter_status  # noqa: E402
from lib.cli_common import bootstrap, echo_info, echo_success, echo_warn, parse_chapter_list, write_json  # noqa: E402
from lib.llm import LLMClient, LLMError, save_prompt_bundle  # noqa: E402
from lib.logging_utils import console, die  # noqa: E402
from lib.prompts import compose_diagram_system, compose_diagram_user  # noqa: E402

app = typer.Typer(
    add_completion=False,
    help="Generate Mermaid diagram sources under diagrams/mermaid/chapter-XXX/.",
    no_args_is_help=True,
)


def _render_pngs(mmd_files: list[Path], png_dir: Path) -> list[Path]:
    mmdc = shutil.which("mmdc")
    if not mmdc:
        raise RuntimeError(
            "mmdc (mermaid-cli) not found. Install with: npm i -g @mermaid-js/mermaid-cli"
        )
    png_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for mmd in mmd_files:
        out = png_dir / f"{mmd.stem}.png"
        subprocess.run(
            [mmdc, "-i", str(mmd), "-o", str(out), "-b", "transparent"],
            check=True,
            capture_output=True,
            text=True,
        )
        written.append(out)
    return written


@app.command()
def main(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c"),
    chapters: Optional[str] = typer.Option(None, "--chapters"),
    start: Optional[int] = typer.Option(None, "--start"),
    end: Optional[int] = typer.Option(None, "--end"),
    extract_only: bool = typer.Option(
        False,
        "--extract-only",
        help="Only extract Mermaid blocks already present in the chapter (no LLM).",
    ),
    force: bool = typer.Option(False, "--force", "-f"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    render: bool = typer.Option(False, "--render", help="Render .mmd to PNG via mermaid-cli."),
    provider: Optional[str] = typer.Option(None, "--provider"),
    model: Optional[str] = typer.Option(None, "--model"),
    config: Optional[Path] = typer.Option(None, "--config"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Generate or extract diagrams for chapters."""
    paths, cfg, curriculum = bootstrap(
        verbose=verbose,
        dry_run=dry_run,
        config=config,
        provider=provider,
        model=model,
    )
    targets = parse_chapter_list(chapter, chapters, start, end, curriculum)
    client = LLMClient(cfg)
    results: list[dict] = []

    for n in targets:
        try:
            meta = curriculum.get(n)
            _, chapter_text = load_chapter(paths, n)
        except (KeyError, FileNotFoundError) as exc:
            die(str(exc))

        out_dir = paths.chapter_diagram_dir(n)
        console.print(
            Panel.fit(
                f"[bold]Chapter {n:03d}[/bold]: {meta.title}\n"
                f"Diagrams: {paths.relative(out_dir)}",
                title="Generate Diagrams",
            )
        )

        blocks = extract_mermaid_blocks(chapter_text)

        if not extract_only:
            system = compose_diagram_system(paths)
            user = compose_diagram_user(paths, number=n, chapter_text=chapter_text)
            bundle_path = paths.state / "prompts" / f"generate-diagrams-{n:03d}.json"
            save_prompt_bundle(
                bundle_path,
                system=system,
                user=user,
                meta={"chapter": n, "extract_only": False, "dry_run": cfg.dry_run},
            )
            echo_info(f"Prompt bundle: {paths.relative(bundle_path)}")

            if cfg.dry_run:
                echo_success(f"Dry-run complete for diagrams of chapter {n:03d}")
                results.append(
                    {
                        "number": n,
                        "status": "dry_run",
                        "existing_blocks": len(blocks),
                    }
                )
                continue

            try:
                response = client.complete(system=system, user=user, temperature=0.2)
            except LLMError as exc:
                die(str(exc))
            generated = extract_mermaid_blocks(response.content)
            if generated:
                blocks = generated
            else:
                echo_warn("LLM returned no mermaid blocks; falling back to chapter extraction.")
        else:
            if cfg.dry_run:
                echo_info(f"Would extract {len(blocks)} diagram(s) from chapter {n:03d}")
                results.append({"number": n, "status": "dry_run", "existing_blocks": len(blocks)})
                continue

        if not blocks:
            echo_warn(f"No Mermaid diagrams found for chapter {n:03d}")
            results.append({"number": n, "status": "empty"})
            continue

        written = write_mermaid_diagrams(paths, n, blocks, force=force)
        pngs: list[str] = []
        if render:
            try:
                png_dir = paths.diagrams_png / f"chapter-{n:03d}"
                rendered = _render_pngs(written, png_dir)
                pngs = [str(p) for p in rendered]
                echo_success(f"Rendered {len(rendered)} PNG(s)")
            except Exception as exc:  # noqa: BLE001
                echo_warn(f"PNG render failed: {exc}")

        update_chapter_status(paths, n, "diagrams_complete", notes="generate_diagrams.py")
        echo_success(f"Wrote {len(written)} diagram source(s) to {paths.relative(out_dir)}")
        results.append(
            {
                "number": n,
                "status": "written",
                "files": [str(p) for p in written],
                "pngs": pngs,
            }
        )

    write_json(paths.reports / "generate_diagrams_last_run.json", {"results": results})


if __name__ == "__main__":
    app()
