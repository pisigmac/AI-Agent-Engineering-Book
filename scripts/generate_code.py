#!/usr/bin/env python3
"""Generate production-quality chapter code packages from MASTER_CODE_GENERATION_PROMPT.

Examples:
  python scripts/generate_code.py --chapter 3 --dry-run
  python scripts/generate_code.py --chapter 14 --force
  python scripts/generate_code.py --chapter 24 --instructions "Focus on FAISS + tests"
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.artifacts import parse_path_fenced_files, write_artifacts  # noqa: E402
from lib.chapter import load_chapter, update_chapter_status  # noqa: E402
from lib.cli_common import bootstrap, echo_info, echo_success, echo_warn, parse_chapter_list, write_json  # noqa: E402
from lib.llm import LLMClient, LLMError, save_prompt_bundle  # noqa: E402
from lib.logging_utils import console, die  # noqa: E402
from lib.prompts import compose_code_system, compose_code_user  # noqa: E402

app = typer.Typer(
    add_completion=False,
    help="Generate modular Python code for a chapter under code/chapter-XXX/.",
    no_args_is_help=True,
)


@app.command()
def main(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c"),
    chapters: Optional[str] = typer.Option(None, "--chapters"),
    start: Optional[int] = typer.Option(None, "--start"),
    end: Optional[int] = typer.Option(None, "--end"),
    instructions: str = typer.Option("", "--instructions", "-i", help="Extra generation guidance."),
    force: bool = typer.Option(False, "--force", "-f"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    model: Optional[str] = typer.Option(None, "--model"),
    config: Optional[Path] = typer.Option(None, "--config"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    max_chapter_chars: int = typer.Option(
        60_000, "--max-chapter-chars", help="Truncate chapter context to this many characters."
    ),
    save_raw: bool = typer.Option(
        True, "--save-raw/--no-save-raw", help="Also save full model output for audit."
    ),
) -> None:
    """Generate code artifacts for chapters."""
    paths, cfg, curriculum = bootstrap(
        verbose=verbose,
        dry_run=dry_run,
        config=config,
        provider=provider,
        model=model,
    )
    targets = parse_chapter_list(chapter, chapters, start, end, curriculum)
    client = LLMClient(cfg)
    system = compose_code_system(paths)
    results: list[dict] = []

    for n in targets:
        try:
            meta = curriculum.get(n)
            _, chapter_text = load_chapter(paths, n)
        except (KeyError, FileNotFoundError) as exc:
            die(str(exc))

        code_dir = paths.chapter_code_dir(n)
        console.print(
            Panel.fit(
                f"[bold]Chapter {n:03d}[/bold]: {meta.title}\n"
                f"Code dir: {paths.relative(code_dir)}",
                title="Generate Code",
            )
        )

        if code_dir.exists() and any(code_dir.rglob("*")) and not force and not cfg.dry_run:
            echo_warn(f"Skipping non-empty {code_dir} (use --force).")
            results.append({"number": n, "status": "skipped_exists"})
            continue

        excerpt = chapter_text[:max_chapter_chars]
        user = compose_code_user(
            paths,
            number=n,
            title=meta.title,
            chapter_excerpt=excerpt,
            instructions=instructions,
        )
        bundle_path = paths.state / "prompts" / f"generate-code-{n:03d}.json"
        save_prompt_bundle(
            bundle_path,
            system=system,
            user=user,
            meta={"chapter": n, "dry_run": cfg.dry_run},
        )
        echo_info(f"Prompt bundle: {paths.relative(bundle_path)}")

        if cfg.dry_run:
            echo_success(f"Dry-run complete for code of chapter {n:03d}")
            results.append({"number": n, "status": "dry_run"})
            continue

        try:
            response = client.complete(system=system, user=user)
        except LLMError as exc:
            die(str(exc))

        if save_raw:
            raw_path = paths.state / "raw" / f"generate-code-{n:03d}.md"
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            raw_path.write_text(response.content, encoding="utf-8")

        artifacts = parse_path_fenced_files(response.content)
        if not artifacts:
            # Fallback: write a single module from the response
            echo_warn("No path-fenced files found; writing code/README + main module fallback.")
            code_dir.mkdir(parents=True, exist_ok=True)
            (code_dir / "GENERATED.md").write_text(response.content, encoding="utf-8")
            (code_dir / "README.md").write_text(
                f"# Chapter {n:03d} — {meta.title}\n\n"
                "Model did not emit path-fenced files. See GENERATED.md and split manually "
                "or re-run with a stronger model / clearer instructions.\n",
                encoding="utf-8",
            )
            written_paths = [code_dir / "GENERATED.md", code_dir / "README.md"]
        else:
            # Normalize paths into chapter code directory when needed
            normalized = []
            from lib.artifacts import FileArtifact

            for art in artifacts:
                rel = art.relative_path.replace("\\", "/")
                if not rel.startswith("code/"):
                    # place under chapter dir
                    rel = f"code/chapter-{n:03d}/{Path(rel).name}"
                elif f"chapter-{n:03d}" not in rel:
                    # force into this chapter package
                    name = Path(rel).name
                    rel = f"code/chapter-{n:03d}/{name}"
                normalized.append(FileArtifact(relative_path=rel, content=art.content))
            written_paths = write_artifacts(paths, normalized, force=force)

        # Ensure README exists
        if not (code_dir / "README.md").is_file():
            code_dir.mkdir(parents=True, exist_ok=True)
            (code_dir / "README.md").write_text(
                f"# Chapter {n:03d} — {meta.title}\n\n"
                "Production code package generated for the AI Agent Engineering Bootcamp.\n\n"
                "## Layout\n\nSee modules in this directory. Prefer pytest for tests.\n",
                encoding="utf-8",
            )

        update_chapter_status(paths, n, "code_complete", notes="generated by generate_code.py")
        echo_success(f"Wrote {len(written_paths)} artifact(s) under {paths.relative(code_dir)}")
        results.append(
            {
                "number": n,
                "status": "written",
                "files": [str(p) for p in written_paths],
                "usage": response.usage,
            }
        )

    write_json(paths.reports / "generate_code_last_run.json", {"results": results})


if __name__ == "__main__":
    app()
