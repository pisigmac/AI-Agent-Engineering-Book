"""Chapter 7 CLI — platform_core composition root demo."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from platform_core.config import Settings
from platform_core.errors import PlatformError
from platform_core.factories import build_container


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def cmd_complete(prompt: str, model: str | None) -> int:
    setup_logging()
    container = build_container(Settings.from_env())
    try:
        record = container.complete_text(prompt, model=model)
    except PlatformError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "run_id": record.run_id,
                "goal": record.goal,
                "output": record.output,
                "created_at": record.created_at,
                "provider": record.provider,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_show_run(run_id: str) -> int:
    setup_logging()
    # New container => empty memory repo. For demo, complete then show is separate.
    # This command documents that repositories are process-scoped unless durable.
    container = build_container(Settings.from_env())
    record = container.runs.get(run_id)
    if record is None:
        print(
            f"Run '{run_id}' not found in this process. "
            "InMemoryRunRepository does not survive process restarts "
            "(swap adapter later for durability).",
            file=sys.stderr,
        )
        return 1
    print(json.dumps(record.__dict__, indent=2, ensure_ascii=False))
    return 0


def cmd_describe() -> int:
    settings = Settings.from_env()
    print("platform_core composition")
    print(f"  app_name={settings.app_name}")
    print(f"  environment={settings.environment}")
    print(f"  provider={settings.provider}")
    print(f"  default_model={settings.default_model}")
    print("  ports: LLMPort, RunRepository, Clock, IdFactory")
    print("  adapters: MockLLMAdapter, InMemoryRunRepository, SystemClock")
    print("  service: CompleteText")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 7 — platform_core CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_complete = sub.add_parser("complete", help="Run CompleteText use case")
    p_complete.add_argument("prompt")
    p_complete.add_argument("--model", default=None)

    p_show = sub.add_parser("show-run", help="Fetch a run from the in-memory repository")
    p_show.add_argument("run_id")

    sub.add_parser("describe", help="Describe wired components")

    args = parser.parse_args(argv)
    if args.cmd == "complete":
        return cmd_complete(args.prompt, args.model)
    if args.cmd == "show-run":
        return cmd_show_run(args.run_id)
    if args.cmd == "describe":
        return cmd_describe()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
