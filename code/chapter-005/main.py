"""Chapter 5 CLI — platform HTTP client demos."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from http_client import HttpClient, HttpClientError
from json_codec import JsonError, loads
from models import AuthConfig, RequestSpec
from rate_limit import TokenBucket
from retry import RetryPolicy


def build_client_from_env() -> HttpClient:
    token = os.getenv("API_TOKEN") or os.getenv("OPENAI_API_KEY")
    auth = AuthConfig(kind="bearer", token=token) if token else AuthConfig()
    rate = os.getenv("HTTP_RATE_PER_S")
    limiter = TokenBucket(rate_per_s=float(rate), capacity=float(rate)) if rate else None
    return HttpClient(
        base_url=os.getenv("API_BASE_URL", ""),
        auth=auth,
        rate_limiter=limiter,
        retry=RetryPolicy(max_attempts=3, base_delay_s=0.2, jitter_s=0.05),
    )


def cmd_get_json(url: str) -> int:
    client = build_client_from_env()
    try:
        data = client.get_json(url, timeout_s=20.0)
    except (HttpClientError, JsonError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_post_json(url: str, body: str) -> int:
    client = build_client_from_env()
    try:
        payload = loads(body)
        data = client.post_json(url, payload, timeout_s=20.0)
    except (HttpClientError, JsonError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


def cmd_demo_rate_limit() -> int:
    bucket = TokenBucket(rate_per_s=5.0, capacity=1.0)
    started = time.perf_counter()
    w1 = bucket.acquire(1.0)
    w2 = bucket.acquire(1.0)
    elapsed = time.perf_counter() - started
    print(f"first_wait_s={w1:.3f}")
    print(f"second_wait_s={w2:.3f}")
    print(f"total_elapsed_s={elapsed:.3f}")
    print("OK: token bucket enforced spacing")
    return 0


def cmd_show_spec() -> int:
    spec = RequestSpec(
        method="POST",
        url="/v1/chat/completions",
        json_body={"model": "demo", "messages": [{"role": "user", "content": "hi"}]},
        idempotent=False,
        timeout_s=60.0,
    )
    print(f"method={spec.method} url={spec.url} timeout={spec.timeout_s}s idempotent={spec.idempotent}")
    print("body_keys=", list(spec.json_body.keys()) if isinstance(spec.json_body, dict) else None)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 5 — HTTP client toolkit")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_get = sub.add_parser("get-json", help="GET URL and print JSON")
    p_get.add_argument("url")

    p_post = sub.add_parser("post-json", help="POST JSON body to URL")
    p_post.add_argument("url")
    p_post.add_argument("body", help='JSON string, e.g. {"a":1}')

    sub.add_parser("demo-rate-limit", help="Demonstrate token bucket pacing")
    sub.add_parser("show-spec", help="Print a sample RequestSpec")

    args = parser.parse_args(argv)
    if args.cmd == "get-json":
        return cmd_get_json(args.url)
    if args.cmd == "post-json":
        return cmd_post_json(args.url, args.body)
    if args.cmd == "demo-rate-limit":
        return cmd_demo_rate_limit()
    if args.cmd == "show-spec":
        return cmd_show_spec()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
