"""Feature placement heuristics for teaching stack instincts."""

from __future__ import annotations

from dataclasses import dataclass

from stack_model import LayerId


@dataclass(frozen=True)
class PlacementDecision:
    layer: LayerId
    rationale: str
    avoid: tuple[LayerId, ...] = ()


def place_feature(description: str) -> PlacementDecision:
    """Heuristic teacher — not production routing.

    Real systems use design review; this function trains instincts.
    """
    text = description.lower()

    if any(k in text for k in ("sla", "cron", "invoice", "etl", "nightly", "pipeline")):
        return PlacementDecision(
            LayerId.WORKFLOW,
            "Procedure looks deterministic; prefer workflow before autonomy.",
            avoid=(LayerId.MULTI_AGENT,),
        )
    if "approve" in text or "human in the loop" in text or "review step" in text:
        return PlacementDecision(
            LayerId.GRAPH,
            "Explicit states/approvals map cleanly to graph nodes and interrupts.",
        )
    if "debate" in text or "multiple roles" in text or "reviewer agent" in text:
        return PlacementDecision(
            LayerId.MULTI_AGENT,
            "Specialized roles imply multi-agent coordination costs—use deliberately.",
        )
    if any(k in text for k in ("research", "investigate", "open-ended", "figure out")):
        return PlacementDecision(
            LayerId.AGENT,
            "Open-ended goals with tool use suggest a policy-bounded agent loop.",
        )
    if any(
        k in text
        for k in ("http", "sql", "email", "browser", "jira", "ticket", "send ")
    ):
        return PlacementDecision(
            LayerId.TOOL,
            "Side effects belong behind typed tool contracts (skills may compose them).",
            avoid=(LayerId.LLM,),
        )
    if any(
        k in text
        for k in ("notion", "pdf", "documentation", "knowledge base", "docs")
    ):
        return PlacementDecision(
            LayerId.RETRIEVAL,
            "Large corpora should be retrieved, not pasted wholesale into prompts.",
        )
    return PlacementDecision(
        LayerId.APPLICATION,
        "Unclear automation shape—start from product requirements, then descend layers.",
        avoid=(LayerId.MULTI_AGENT,),
    )
