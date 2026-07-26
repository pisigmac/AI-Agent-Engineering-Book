"""Sample support knowledge base for the semantic-search mini project."""

from __future__ import annotations

from embedkit.types import Document

# Intentionally written so paraphrases differ from titles—tests rely on meaning-ish overlap
# under hashing embeddings (shared stems / character n-grams), not exact title match.

SUPPORT_FAQS: list[Document] = [
    Document(
        id="faq-refund",
        text=(
            "Refund policy: customers may reverse a charge or request money back within "
            "30 days of purchase if the product is unused. Chargebacks follow the same "
            "window. Contact billing to start a refund."
        ),
        metadata={"topic": "billing", "title": "Refunds"},
    ),
    Document(
        id="faq-shipping",
        text=(
            "Shipping times: standard delivery takes 5–7 business days. Express shipping "
            "arrives in 2 business days. Tracking numbers are emailed after dispatch."
        ),
        metadata={"topic": "logistics", "title": "Shipping"},
    ),
    Document(
        id="faq-auth",
        text=(
            "Account access: reset your password from the login page. Enable two-factor "
            "authentication for security. Locked accounts unlock after identity verification."
        ),
        metadata={"topic": "security", "title": "Authentication"},
    ),
    Document(
        id="faq-cancel",
        text=(
            "Subscription cancellation: you can stop auto-renewal in settings at any time. "
            "Access continues until the end of the paid period. No partial-period refunds "
            "except where required by law."
        ),
        metadata={"topic": "billing", "title": "Cancel subscription"},
    ),
    Document(
        id="faq-privacy",
        text=(
            "Privacy: we store account email and usage metrics. You may export or delete "
            "personal data from the privacy center. Support ticket contents are confidential "
            "and access is limited to authorized staff."
        ),
        metadata={"topic": "legal", "title": "Privacy"},
    ),
    Document(
        id="faq-api",
        text=(
            "API rate limits: free tier allows 60 requests per minute. Paid plans raise "
            "limits. HTTP 429 means back off and retry with exponential delay."
        ),
        metadata={"topic": "developers", "title": "API limits"},
    ),
]


def load_support_corpus() -> list[Document]:
    return list(SUPPORT_FAQS)
