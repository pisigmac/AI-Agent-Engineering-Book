"""Tests for the Chapter 2 architecture atlas."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from canonical_stack import build_canonical_stack
from placement import place_feature
from stack_model import LayerId


def test_stack_dependencies_valid():
    stack = build_canonical_stack()
    assert stack.validate_dependencies() == []


def test_expected_layer_count():
    stack = build_canonical_stack()
    assert len(stack.layers) == 16


def test_application_depends_on_harness_and_observability():
    app = build_canonical_stack().get(LayerId.APPLICATION)
    assert LayerId.HARNESS in app.depends_on
    assert LayerId.OBSERVABILITY in app.depends_on


def test_agent_depends_on_core_capabilities():
    agent = build_canonical_stack().get(LayerId.AGENT)
    for required in (LayerId.LLM, LayerId.SKILL, LayerId.PLANNER, LayerId.MEMORY):
        assert required in agent.depends_on


def test_placement_workflow():
    decision = place_feature("Nightly invoice reconciliation pipeline")
    assert decision.layer == LayerId.WORKFLOW


def test_placement_agent():
    decision = place_feature("Open-ended market research investigation")
    assert decision.layer == LayerId.AGENT


def test_placement_retrieval():
    decision = place_feature("Answer questions from PDF documentation knowledge base")
    assert decision.layer == LayerId.RETRIEVAL


def test_mermaid_export_contains_edges():
    mermaid = build_canonical_stack().to_mermaid()
    assert "flowchart BT" in mermaid
    assert "llm -->" in mermaid or "skill -->" in mermaid
    assert "harness" in mermaid
