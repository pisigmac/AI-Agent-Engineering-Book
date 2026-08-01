"""Knowledge base documents for the assistant mini project."""

from __future__ import annotations

KB_DOCS: list[dict] = [
    {
        "id": "kb-refund",
        "text": (
            "Refund policy: customers may reverse a charge or request money back within "
            "30 days of purchase for unused products. Contact billing to start a refund."
        ),
        "metadata": {"topic": "billing", "product": "core", "title": "Refunds"},
    },
    {
        "id": "kb-cancel",
        "text": (
            "Cancel subscription in account settings at any time. Access continues until "
            "the end of the paid period. Partial refunds only where required by law."
        ),
        "metadata": {"topic": "billing", "product": "core", "title": "Cancel"},
    },
    {
        "id": "kb-shipping",
        "text": (
            "Shipping: standard delivery takes 5-7 business days. Express arrives in 2 days. "
            "Tracking numbers are emailed after the package ships."
        ),
        "metadata": {"topic": "logistics", "product": "retail", "title": "Shipping"},
    },
    {
        "id": "kb-auth",
        "text": (
            "Reset your password from the login page. Enable two-factor authentication "
            "for stronger security. Locked accounts unlock after identity verification."
        ),
        "metadata": {"topic": "security", "product": "core", "title": "Authentication"},
    },
    {
        "id": "kb-sso",
        "text": (
            "Enterprise SSO supports SAML and OIDC. Map groups to roles in the admin console. "
            "Session length is configurable per organization."
        ),
        "metadata": {"topic": "security", "product": "enterprise", "title": "SSO"},
    },
    {
        "id": "kb-api",
        "text": (
            "API rate limits: free tier allows 60 requests per minute. HTTP 429 means back off "
            "and retry with exponential delay. Check the Retry-After header."
        ),
        "metadata": {"topic": "developers", "product": "api", "title": "Rate limits"},
    },
    {
        "id": "kb-privacy",
        "text": (
            "Privacy: export or delete personal data from the privacy center. Support tickets "
            "and embedding vectors of customer content are confidential."
        ),
        "metadata": {"topic": "legal", "product": "core", "title": "Privacy"},
    },
    {
        "id": "kb-sla",
        "text": (
            "Enterprise SLA targets 99.9% monthly uptime excluding planned maintenance. "
            "Service credits apply after investigation when availability falls below target."
        ),
        "metadata": {"topic": "legal", "product": "enterprise", "title": "SLA"},
    },
]


def knowledge_docs() -> list[dict]:
    return list(KB_DOCS)
