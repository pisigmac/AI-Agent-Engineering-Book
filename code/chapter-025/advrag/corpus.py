"""Enterprise knowledge corpus with long parent documents."""

from __future__ import annotations

from advrag.parent_child import ParentChildIndex, split_parent_children
from advrag.types import Document

PARENTS: list[Document] = [
    Document(
        id="parent-billing",
        text=(
            "Billing Handbook. Refund policy: customers may reverse a charge or request money back "
            "within 30 days of purchase for unused products. Contact billing to start a refund. "
            "Chargebacks follow the same window. Subscription cancellation: stop auto-renewal in "
            "settings at any time. Access continues until the paid period ends. Partial refunds "
            "apply only where required by law. Invoices are emailed monthly to the billing contact."
        ),
        metadata={"title": "Billing Handbook", "topic": "billing", "org": "acme"},
    ),
    Document(
        id="parent-logistics",
        text=(
            "Logistics Guide. Shipping: standard delivery takes 5-7 business days. Express arrives "
            "in 2 business days. Tracking numbers are emailed after dispatch. Returns need the "
            "prepaid label within 14 days of delivery. Warehouse processing happens on business days. "
            "International customs delays are outside the standard SLA."
        ),
        metadata={"title": "Logistics Guide", "topic": "logistics", "org": "acme"},
    ),
    Document(
        id="parent-security",
        text=(
            "Security Manual. Reset your password from the login page. Enable two-factor authentication "
            "for stronger security. Locked accounts unlock after identity verification. Enterprise SSO "
            "supports SAML and OIDC single sign-on. Map groups to roles in the admin console. API keys "
            "must be rotated regularly and never embedded in mobile apps."
        ),
        metadata={"title": "Security Manual", "topic": "security", "org": "acme"},
    ),
    Document(
        id="parent-platform",
        text=(
            "Platform Developer Notes. API rate limits: free tier allows 60 requests per minute. "
            "HTTP 429 means back off and retry with exponential delay. Check the Retry-After header. "
            "RAG systems retrieve knowledge chunks and ground answers in evidence. Hybrid search "
            "combines BM25 keyword matching with dense embedding retrieval for better recall."
        ),
        metadata={"title": "Platform Notes", "topic": "developers", "org": "acme"},
    ),
    Document(
        id="parent-legal",
        text=(
            "Legal Policies. Privacy: export or delete personal data from the privacy center. "
            "Customer content and embedding vectors are confidential. Enterprise SLA targets 99.9% "
            "monthly uptime excluding planned maintenance. Service credits apply after investigation "
            "when availability falls below the contractual target."
        ),
        metadata={"title": "Legal Policies", "topic": "legal", "org": "acme"},
    ),
]


def build_parent_child_index() -> ParentChildIndex:
    pci = ParentChildIndex()
    for parent in PARENTS:
        kids = split_parent_children(parent, child_size=160, overlap=40)
        pci.add_parent(parent, kids)
    return pci


def all_children() -> list[Document]:
    return build_parent_child_index().all_indexable()
