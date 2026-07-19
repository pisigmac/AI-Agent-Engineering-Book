"""Controllable mock LLM for teaching failure modes offline."""

from __future__ import annotations

from enum import Enum

from llm_concepts.messages import CompletionResult


class MockMode(str, Enum):
    ECHO = "echo"
    GROUNDED = "grounded"
    HALLUCINATE = "hallucinate"


class MockLLM:
    """Deterministic stand-in for a hosted model API."""

    def __init__(self, *, mode: MockMode = MockMode.ECHO, model_name: str = "mock-llm-8") -> None:
        self.mode = mode
        self.model_name = model_name

    def complete(self, prompt: str, *, context: str | None = None) -> CompletionResult:
        prompt = prompt.strip()
        tokens = max(1, len(prompt.split()))
        if self.mode is MockMode.HALLUCINATE:
            text = (
                "According to Internal Policy Case 99-ZZZ (2024), all refunds are "
                "guaranteed within 365 days with no receipt. "
                f"Regarding your question: {prompt}"
            )
            return CompletionResult(
                text=text,
                model=self.model_name,
                mode=self.mode.value,
                grounded=False,
                usage_tokens=tokens + 20,
            )
        if self.mode is MockMode.GROUNDED:
            if not context or not context.strip():
                text = (
                    "I do not have supporting context for that question. "
                    "Please provide a source document or use retrieval."
                )
                return CompletionResult(
                    text=text,
                    model=self.model_name,
                    mode=self.mode.value,
                    grounded=False,
                    usage_tokens=tokens + 8,
                )
            # Naive extractive answer: prefer sentences overlapping query terms.
            answer = _extractive_answer(prompt, context)
            if answer is None:
                text = (
                    "The provided context does not contain enough information "
                    "to answer that question."
                )
                grounded = False
            else:
                text = answer
                grounded = True
            return CompletionResult(
                text=text,
                model=self.model_name,
                mode=self.mode.value,
                grounded=grounded,
                usage_tokens=tokens + len(text.split()),
            )
        # ECHO
        return CompletionResult(
            text=f"ECHO: {prompt}",
            model=self.model_name,
            mode=self.mode.value,
            grounded=False,
            usage_tokens=tokens,
        )


def _extractive_answer(question: str, context: str) -> str | None:
    q_terms = {t.lower() for t in question.split() if len(t) > 3}
    best: tuple[int, str] | None = None
    for raw in context.replace("!", ".").replace("?", ".").split("."):
        sentence = raw.strip()
        if not sentence:
            continue
        s_terms = {t.lower().strip(",.;:") for t in sentence.split()}
        score = len(q_terms & s_terms)
        if score <= 0:
            continue
        if best is None or score > best[0]:
            best = (score, sentence)
    if best is None:
        return None
    return best[1] + "."
