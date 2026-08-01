"""Labeled corpus for hybrid evaluation."""
from __future__ import annotations
from hybridret.types import Document

DOCS = [
    Document("d-refund", "Refund policy: reverse a charge or money back within 30 days for unused products.", {"topic": "billing"}),
    Document("d-cancel", "Cancel subscription in settings; access continues until period end.", {"topic": "billing"}),
    Document("d-ship", "Shipping tracking numbers emailed after dispatch; express 2 business days.", {"topic": "logistics"}),
    Document("d-auth", "Reset password on login page; enable two-factor authentication.", {"topic": "security"}),
    Document("d-api", "API rate limits free tier 60 rpm; HTTP 429 means backoff retry.", {"topic": "developers"}),
    Document("d-sso", "Enterprise SAML OIDC single sign-on maps groups to roles.", {"topic": "security"}),
    Document("d-privacy", "Export or delete personal data from privacy center; content confidential.", {"topic": "legal"}),
    Document("d-sla", "SLA 99.9 percent monthly uptime excluding planned maintenance credits.", {"topic": "legal"}),
    Document("d-error", "Error code E-4032 means payment gateway timeout; retry with idempotency key.", {"topic": "developers"}),
    Document("d-hybrid", "Hybrid search combines BM25 keyword matching with dense embedding retrieval.", {"topic": "developers"}),
]

# query -> relevant doc ids
LABELS = [
    ("How do I get my money back?", ("d-refund",)),
    ("HTTP 429 rate limit", ("d-api",)),
    ("error code E-4032", ("d-error",)),
    ("forgot password two-factor", ("d-auth",)),
    ("SAML SSO enterprise", ("d-sso",)),
    ("tracking number package", ("d-ship",)),
    ("what is hybrid search", ("d-hybrid",)),
    ("delete my personal data", ("d-privacy",)),
]
