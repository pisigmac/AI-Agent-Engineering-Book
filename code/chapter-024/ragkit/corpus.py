"""Knowledge corpus for the production RAG system."""

from __future__ import annotations

from ragkit.types import Document

CORPUS: list[Document] = [
    Document(
        id="doc-refund",
        text=(
            "Refund policy: customers may reverse a charge or request money back within "
            "30 days of purchase for unused products. Contact billing to start a refund."
        ),
        metadata={"title": "Refund Policy", "topic": "billing", "source": "handbook"},
    ),
    Document(
        id="doc-cancel",
        text=(
            "Subscription cancellation: stop auto-renewal in settings at any time. "
            "Access continues until the paid period ends."
        ),
        metadata={"title": "Cancel Subscription", "topic": "billing", "source": "handbook"},
    ),
    Document(
        id="doc-shipping",
        text=(
            "Shipping: standard delivery takes 5-7 business days. Express arrives in 2 days. "
            "Tracking numbers are emailed after dispatch."
        ),
        metadata={"title": "Shipping", "topic": "logistics", "source": "handbook"},
    ),
    Document(
        id="doc-auth",
        text=(
            "Account access: reset your password from the login page. Enable two-factor "
            "authentication. Locked accounts unlock after identity verification."
        ),
        metadata={"title": "Authentication", "topic": "security", "source": "handbook"},
    ),
    Document(
        id="doc-api",
        text=(
            "API rate limits: free tier allows 60 requests per minute. HTTP 429 means back off "
            "and retry with exponential delay."
        ),
        metadata={"title": "API Limits", "topic": "developers", "source": "handbook"},
    ),
    Document(
        id="doc-privacy",
        text=(
            "Privacy: export or delete personal data from the privacy center. Customer content "
            "and vectors are confidential."
        ),
        metadata={"title": "Privacy", "topic": "legal", "source": "handbook"},
    ),
    Document(
        id="doc-sla",
        text=(
            "Enterprise SLA targets 99.9% monthly uptime excluding planned maintenance. "
            "Credits apply after investigation when availability is below target."
        ),
        metadata={"title": "SLA", "topic": "legal", "source": "handbook"},
    ),
    Document(
        id="doc-rag",
        text=(
            "RAG systems retrieve knowledge chunks, assemble prompts with citations, and "
            "generate answers grounded in evidence rather than model memory alone."
        ),
        metadata={"title": "About RAG", "topic": "developers", "source": "handbook"},
    ),
]


def load_corpus() -> list[Document]:
    return list(CORPUS)
