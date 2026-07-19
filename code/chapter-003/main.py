"""Chapter 3 CLI — pyutils demos."""

from __future__ import annotations

import argparse
import json

from pyutils.contexts import timer_span
from pyutils.decorators import retry, timed
from pyutils.errors import TransientError
from pyutils.iterutils import batched
from pyutils.result import Err, Ok
from pyutils.text import clamp, slugify, truncate
from pyutils.types import Message, WhitespaceTokenizer


@timed
def _hashish(text: str) -> int:
    return sum(ord(ch) for ch in text)


def cmd_demo() -> int:
    msg = Message(role="user", content="Explain tool boundaries")
    tokens = WhitespaceTokenizer().tokenize(msg.content)
    with timer_span("demo") as span:
        value = clamp(1.7, lo=0.0, hi=1.0)
        short = truncate(msg.content, 20)
        result: Ok[str] | Err[str] = Ok("ready").map(lambda s: s.upper())
    print(
        json.dumps(
            {
                "message": {"role": msg.role, "content": msg.content},
                "tokens": tokens,
                "temperature": value,
                "truncated": short,
                "result": result.value if isinstance(result, Ok) else None,
                "span_s": round(span.elapsed_s, 6),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_slug(text: str) -> int:
    print(slugify(text))
    return 0


def cmd_batch(size: int, items: list[str]) -> int:
    for i, batch in enumerate(batched(items, size), start=1):
        print(f"batch-{i}: {batch}")
    return 0


def cmd_retry_demo() -> int:
    state = {"n": 0}

    @retry(attempts=3, delay_s=0.0)
    def flaky() -> str:
        state["n"] += 1
        if state["n"] < 3:
            raise TransientError("temporary glitch")
        return "ok"

    print(flaky())
    print(f"attempts={state['n']}")
    _hashish("abc")
    print(f"timed_elapsed_s={getattr(_hashish, 'last_elapsed_s', 0):.6f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 3 — pyutils CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo", help="Run a combined utilities demo")
    p_slug = sub.add_parser("slug", help="Slugify text")
    p_slug.add_argument("text")
    p_batch = sub.add_parser("batch", help="Batch items")
    p_batch.add_argument("size", type=int)
    p_batch.add_argument("items", nargs="+")
    sub.add_parser("retry-demo", help="Demonstrate retry decorator")

    args = parser.parse_args(argv)
    if args.cmd == "demo":
        return cmd_demo()
    if args.cmd == "slug":
        return cmd_slug(args.text)
    if args.cmd == "batch":
        return cmd_batch(args.size, args.items)
    if args.cmd == "retry-demo":
        return cmd_retry_demo()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
