"""Sample knowledge docs for the mini vector DB."""

from __future__ import annotations

DOCS: list[dict] = [
    {
        "id": "refund",
        "text": "Refund policy: reverse a charge or money back within 30 days for unused products.",
        "metadata": {"topic": "billing", "tenant": "acme", "priority": 1},
    },
    {
        "id": "cancel",
        "text": "Cancel subscription in settings; access continues until period end.",
        "metadata": {"topic": "billing", "tenant": "acme", "priority": 2},
    },
    {
        "id": "shipping",
        "text": "Standard shipping 5-7 days; express in 2 days; tracking emailed after dispatch.",
        "metadata": {"topic": "logistics", "tenant": "acme", "priority": 1},
    },
    {
        "id": "auth",
        "text": "Reset password on login page; enable two-factor authentication for security.",
        "metadata": {"topic": "security", "tenant": "acme", "priority": 1},
    },
    {
        "id": "sso",
        "text": "Enterprise SAML and OIDC single sign-on maps groups to roles.",
        "metadata": {"topic": "security", "tenant": "globex", "priority": 2},
    },
    {
        "id": "api",
        "text": "API rate limits 60 rpm free tier; HTTP 429 means backoff and retry.",
        "metadata": {"topic": "developers", "tenant": "acme", "priority": 1},
    },
    {
        "id": "privacy",
        "text": "Export or delete personal data from the privacy center; content is confidential.",
        "metadata": {"topic": "legal", "tenant": "acme", "priority": 3},
    },
    {
        "id": "sla",
        "text": "Enterprise SLA targets 99.9 percent monthly uptime excluding maintenance.",
        "metadata": {"topic": "legal", "tenant": "globex", "priority": 2},
    },
]

QUERIES = [
    "How do I get my money back?",
    "Where is my package tracking?",
    "forgot password two-factor",
    "HTTP 429 rate limit",
    "SAML SSO enterprise",
]
