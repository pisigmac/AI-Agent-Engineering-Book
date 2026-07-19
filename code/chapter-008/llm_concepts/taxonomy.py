"""Capability and risk taxonomy for LLM systems engineering."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TrainingPhase(str, Enum):
    PRETRAINING = "pretraining"
    POST_TRAINING = "post_training"
    INFERENCE = "inference"


class Capability(str, Enum):
    GENERATION = "generation"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"
    SUMMARIZATION = "summarization"
    TOOL_INTENT = "tool_intent"
    CODE = "code"


class RiskClass(str, Enum):
    HALLUCINATION = "hallucination"
    STALE_KNOWLEDGE = "stale_knowledge"
    NON_DETERMINISM = "non_determinism"
    PROMPT_INJECTION = "prompt_injection"
    OVERCONFIDENCE = "overconfidence"
    CONTEXT_OVERFLOW = "context_overflow"


@dataclass(frozen=True)
class PhaseInfo:
    phase: TrainingPhase
    summary: str
    owner: str


PHASES: tuple[PhaseInfo, ...] = (
    PhaseInfo(
        TrainingPhase.PRETRAINING,
        "Learn general next-token patterns from large corpora.",
        "Model labs / vendors",
    ),
    PhaseInfo(
        TrainingPhase.POST_TRAINING,
        "Shape instruction following, preferences, and tool behavior.",
        "Vendors / fine-tuners",
    ),
    PhaseInfo(
        TrainingPhase.INFERENCE,
        "Online token generation under latency, cost, and safety constraints.",
        "Application engineers (you)",
    ),
)


CAPABILITY_NOTES: dict[Capability, str] = {
    Capability.GENERATION: "Draft text, plans, and explanations.",
    Capability.CLASSIFICATION: "Route intents and label content.",
    Capability.EXTRACTION: "Pull fields from messy text.",
    Capability.SUMMARIZATION: "Compress context for downstream steps.",
    Capability.TOOL_INTENT: "Propose tool calls (must be validated/executed).",
    Capability.CODE: "Generate or edit code (verify with tests).",
}


RISK_NOTES: dict[RiskClass, str] = {
    RiskClass.HALLUCINATION: "Fluent claims without supporting evidence.",
    RiskClass.STALE_KNOWLEDGE: "Weights lack live facts after cutoff.",
    RiskClass.NON_DETERMINISM: "Outputs vary across samples/versions.",
    RiskClass.PROMPT_INJECTION: "Untrusted text overrides instructions.",
    RiskClass.OVERCONFIDENCE: "Certain tone without calibrated uncertainty.",
    RiskClass.CONTEXT_OVERFLOW: "Critical instructions fall out of window.",
}


def explain_llm() -> dict[str, object]:
    return {
        "definition": (
            "An LLM is a parameterized model that predicts and generates tokens "
            "conditioned on context; applications must treat outputs as untrusted "
            "until grounded or verified."
        ),
        "phases": [
            {"phase": p.phase.value, "summary": p.summary, "owner": p.owner} for p in PHASES
        ],
        "capabilities": [
            {"id": c.value, "note": CAPABILITY_NOTES[c]} for c in Capability
        ],
        "risks": [{"id": r.value, "note": RISK_NOTES[r]} for r in RiskClass],
    }
