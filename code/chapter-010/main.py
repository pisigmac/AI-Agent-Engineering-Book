"""Chapter 10 CLI — token calculator, cost, packer, agent report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from token_kit.accounting import UsageLedger
from token_kit.budget import effective_input_budget, utilization
from token_kit.packer import ContextPacker
from token_kit.pricing import PriceTable, estimate_cost
from token_kit.tokenizers import ApproxCl100kCounter, CharHeuristicCounter, get_default_counter
from token_kit.types import BudgetConfig, ChatMessage, Role, TokenUsage


def _load_messages(path: Path) -> list[ChatMessage]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    messages: list[ChatMessage] = []
    for i, item in enumerate(raw):
        messages.append(
            ChatMessage(
                role=Role(item["role"]),
                content=item["content"],
                name=item.get("name"),
                message_id=item.get("message_id", f"m{i}"),
                priority=item.get("priority"),
                metadata=item.get("metadata") or {},
            )
        )
    return messages


def cmd_count(text: str, backend: str) -> int:
    counter = (
        CharHeuristicCounter()
        if backend == "char"
        else ApproxCl100kCounter()
        if backend == "approx"
        else get_default_counter(prefer_tiktoken=backend == "tiktoken")
    )
    n = counter.count_text(text)
    print(json.dumps({"tokenizer": counter.name, "tokens": n, "chars": len(text)}, indent=2))
    return 0


def cmd_cost(model: str, input_tokens: int, output_tokens: int) -> int:
    table = PriceTable()
    price = table.get(model)
    usage = TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens)
    cost = estimate_cost(usage, price)
    print(
        json.dumps(
            {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "input_per_mtok": price.input_per_mtok,
                "output_per_mtok": price.output_per_mtok,
                "cost_usd_est": round(cost, 6),
                "context_window": price.context_window,
            },
            indent=2,
        )
    )
    return 0


def cmd_pack(messages_file: Path, budget: int, max_completion: int) -> int:
    messages = _load_messages(messages_file)
    counter = ApproxCl100kCounter()
    packer = ContextPacker(counter)
    config = BudgetConfig(context_window=budget + max_completion + 64, max_completion=max_completion, margin=64)
    # If user passes absolute budget for input, honor via synthetic window
    config = BudgetConfig(
        context_window=budget + max_completion + 64,
        max_completion=max_completion,
        margin=64,
    )
    # Override: set window so effective == budget
    # effective = window - completion - margin => window = budget + completion + margin
    result = packer.pack(messages, config)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    return 1 if result.over_budget else 0


def cmd_agent_report(messages_file: Path, window: int, model: str) -> int:
    messages = _load_messages(messages_file)
    counter = ApproxCl100kCounter()
    table = PriceTable()
    price = table.get(model)
    config = BudgetConfig(context_window=window, max_completion=1024, margin=256)
    packer = ContextPacker(counter)
    packed = packer.pack(messages, config)
    usage = TokenUsage(
        input_tokens=packed.tokens_est,
        output_tokens=config.max_completion // 4,  # illustrative expected output
        tokenizer=counter.name,
    )
    ledger = UsageLedger()
    ledger.add("pack_preflight", usage, model=model, dropped=len(packed.dropped))
    report = {
        "model": model,
        "window": window,
        "effective_input_budget": effective_input_budget(config),
        "utilization": round(utilization(packed.tokens_est, config), 4),
        "pack": packed.to_dict(),
        "illustrative_step_cost_usd": round(estimate_cost(usage, price), 6),
        "ledger": ledger.to_dict(price),
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def cmd_list_models() -> int:
    print(json.dumps({"models": PriceTable().list_models()}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 10 — token calculator & packer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_count = sub.add_parser("count", help="Count tokens in text")
    p_count.add_argument("--text", required=True)
    p_count.add_argument("--backend", choices=["approx", "char", "tiktoken"], default="approx")

    p_cost = sub.add_parser("cost", help="Estimate USD cost")
    p_cost.add_argument("--model", default="gpt-4.1")
    p_cost.add_argument("--input", dest="input_tokens", type=int, required=True)
    p_cost.add_argument("--output", dest="output_tokens", type=int, default=0)

    p_pack = sub.add_parser("pack", help="Pack messages into a token budget")
    p_pack.add_argument("--messages-file", type=Path, required=True)
    p_pack.add_argument("--budget", type=int, default=800, help="Target effective input budget")
    p_pack.add_argument("--max-completion", type=int, default=256)

    p_rep = sub.add_parser("agent-report", help="Full preflight report for a transcript")
    p_rep.add_argument("--messages-file", type=Path, required=True)
    p_rep.add_argument("--window", type=int, default=8192)
    p_rep.add_argument("--model", default="gpt-4.1-mini")

    sub.add_parser("list-models", help="List illustrative price table models")

    args = parser.parse_args(argv)
    if args.cmd == "count":
        return cmd_count(args.text, args.backend)
    if args.cmd == "cost":
        return cmd_cost(args.model, args.input_tokens, args.output_tokens)
    if args.cmd == "pack":
        return cmd_pack(args.messages_file, args.budget, args.max_completion)
    if args.cmd == "agent-report":
        return cmd_agent_report(args.messages_file, args.window, args.model)
    if args.cmd == "list-models":
        return cmd_list_models()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
