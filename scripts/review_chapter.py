#!/usr/bin/env python3
"""Review chapter drafts against MASTER_REVIEW_PROMPT and source-of-truth docs.

Examples:
  python scripts/review_chapter.py --chapter 1
  python scripts/review_chapter.py --chapters 1-5 --dry-run
  python scripts/review_chapter.py --chapter 3 --focus security
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.chapter import load_chapter, update_chapter_status  # noqa: E402
from lib.cli_common import bootstrap, echo_info, echo_success, parse_chapter_list, write_json  # noqa: E402
from lib.llm import LLMClient, LLMError, save_prompt_bundle  # noqa: E402
from lib.logging_utils import console, die  # noqa: E402
from lib.prompts import compose_review_system, compose_review_user  # noqa: E402

app = typer.Typer(
    add_completion=False,
    help="Produce O'Reilly-grade structured chapter reviews.",
    no_args_is_help=True,
)


def _extract_recommendation(review_text: str) -> str | None:
    match = re.search(
        r"Final Recommendation.*?(Accept(?: with Minor Revisions)?|Major Revisions Required|Reject)",
        review_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else None


@app.command()
def main(
    chapter: Optional[int] = typer.Option(None, "--chapter", "-c"),
    chapters: Optional[str] = typer.Option(None, "--chapters"),
    start: Optional[int] = typer.Option(None, "--start"),
    end: Optional[int] = typer.Option(None, "--end"),
    focus: str = typer.Option(
        "full",
        "--focus",
        help="Review focus: full | technical | security | editorial | pedagogy | code",
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
    provider: Optional[str] = typer.Option(None, "--provider"),
    model: Optional[str] = typer.Option(None, "--model"),
    config: Optional[Path] = typer.Option(None, "--config"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing review files."),
) -> None:
    """Review one or more chapters into reviews/chapter-XXX-review.md."""
    paths, cfg, curriculum = bootstrap(
        verbose=verbose,
        dry_run=dry_run,
        config=config,
        provider=provider,
        model=model,
    )
    targets = parse_chapter_list(chapter, chapters, start, end, curriculum)
    client = LLMClient(cfg)
    system = compose_review_system(paths)
    results: list[dict] = []

    for n in targets:
        try:
            meta = curriculum.get(n)
            chapter_path, chapter_text = load_chapter(paths, n)
        except (KeyError, FileNotFoundError) as exc:
            die(str(exc))

        review_path = paths.chapter_review(n)
        console.print(
            Panel.fit(
                f"[bold]Chapter {n:03d}[/bold]: {meta.title}\n"
                f"Source: {paths.relative(chapter_path)}\n"
                f"Review: {paths.relative(review_path)}\n"
                f"Focus: {focus}",
                title="Review Chapter",
            )
        )

        if review_path.exists() and not force and not cfg.dry_run:
            echo_info(f"Review exists: {review_path.name} (use --force to overwrite)")
            results.append({"number": n, "status": "skipped_exists"})
            continue

        user = compose_review_user(paths, number=n, chapter_text=chapter_text, focus=focus)
        bundle_path = paths.state / "prompts" / f"review-chapter-{n:03d}.json"
        save_prompt_bundle(
            bundle_path,
            system=system,
            user=user,
            meta={"chapter": n, "focus": focus, "dry_run": cfg.dry_run},
        )
        echo_info(f"Prompt bundle: {paths.relative(bundle_path)}")

        if cfg.dry_run:
            echo_success(f"Dry-run complete for review of chapter {n:03d}")
            results.append({"number": n, "status": "dry_run"})
            continue

        try:
            response = client.complete(system=system, user=user)
        except LLMError as exc:
            die(str(exc))

        paths.reviews.mkdir(parents=True, exist_ok=True)
        header = (
            f"# Review: Chapter {n:03d} — {meta.title}\n\n"
            f"- Focus: `{focus}`\n"
            f"- Model: `{response.model}`\n"
            f"- Provider: `{response.provider}`\n\n---\n\n"
        )
        review_path.write_text(header + response.content.strip() + "\n", encoding="utf-8")
        recommendation = _extract_recommendation(response.content)
        update_chapter_status(
            paths,
            n,
            "reviewed",
            notes=f"review recommendation: {recommendation or 'n/a'}",
        )
        echo_success(f"Wrote {paths.relative(review_path)}")
        if recommendation:
            echo_info(f"Recommendation: {recommendation}")

        results.append(
            {
                "number": n,
                "status": "reviewed",
                "path": str(review_path),
                "recommendation": recommendation,
                "usage": response.usage,
            }
        )

    write_json(paths.reports / "review_chapter_last_run.json", {"results": results})


if __name__ == "__main__":
    app()
