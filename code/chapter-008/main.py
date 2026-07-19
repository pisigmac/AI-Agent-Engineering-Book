"""Chapter 8 CLI — LLM concept lab."""

from __future__ import annotations

import argparse
import json
import sys

from llm_concepts.eval_basic import evaluate_answer
from llm_concepts.grounding import GroundedQA, default_policy_corpus
from llm_concepts.mock_llm import MockLLM, MockMode
from llm_concepts.taxonomy import explain_llm


def cmd_explain() -> int:
    print(json.dumps(explain_llm(), indent=2))
    return 0


def cmd_ask(question: str, mode: str) -> int:
    if mode == "grounded":
        qa = GroundedQA(default_policy_corpus())
        result, docs = qa.ask(question)
        payload = {
            "question": question,
            "mode": mode,
            "answer": result.text,
            "grounded": result.grounded,
            "model": result.model,
            "docs": [{"id": d.doc_id, "title": d.title} for d in docs],
        }
    else:
        llm = MockLLM(mode=MockMode(mode))
        result = llm.complete(question)
        payload = {
            "question": question,
            "mode": mode,
            "answer": result.text,
            "grounded": result.grounded,
            "model": result.model,
            "docs": [],
        }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def cmd_eval_demo() -> int:
    store = default_policy_corpus()
    qa = GroundedQA(store)
    grounded_q = "What is the refund window?"
    grounded_result, docs = qa.ask(grounded_q)
    grounded_ctx = "\n".join(d.text for d in docs)
    grounded_report = evaluate_answer(
        grounded_result, context=grounded_ctx, expect_grounded=True
    )

    hallu = MockLLM(mode=MockMode.HALLUCINATE).complete(grounded_q)
    hallu_report = evaluate_answer(hallu, context=None, expect_grounded=False)

    unanswerable = qa.ask("What is the CEO's pet name?")[0]
    unans_report = evaluate_answer(unanswerable, context=store.all_text(), expect_grounded=True)

    print(
        json.dumps(
            {
                "grounded_answer": grounded_result.text,
                "grounded_eval": grounded_report.to_dict(),
                "hallucinated_answer": hallu.text,
                "hallucinated_eval": hallu_report.to_dict(),
                "unanswerable_answer": unanswerable.text,
                "unanswerable_eval": unans_report.to_dict(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    # Exit 0 even if hallu fails eval — demo should show the failure.
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chapter 8 — LLM concept lab")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("explain", help="Print LLM taxonomy and definition")
    p_ask = sub.add_parser("ask", help="Ask the mock LLM")
    p_ask.add_argument("question")
    p_ask.add_argument(
        "--mode",
        choices=[m.value for m in MockMode] + ["grounded"],
        default="grounded",
    )
    sub.add_parser("eval-demo", help="Compare grounded vs hallucinated eval reports")

    args = parser.parse_args(argv)
    if args.cmd == "explain":
        return cmd_explain()
    if args.cmd == "ask":
        return cmd_ask(args.question, args.mode)
    if args.cmd == "eval-demo":
        return cmd_eval_demo()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
