"""Sample long documents for the chunk visualizer mini project."""

from __future__ import annotations

from chunkkit.types import SourceDocument

POLICY_HANDBOOK = """# Acme Platform Policy Handbook

## 1. Introduction

Welcome to the Acme Platform. This handbook explains billing, security, and developer policies.
It is intentionally long so chunking strategies produce visible boundaries.

## 2. Billing and Refunds

Customers may request a refund or reverse a charge within 30 days of purchase for unused products.
Chargebacks follow the same window. Contact billing to start a money-back request.

Subscriptions renew automatically unless cancelled in settings. Access continues until the period ends.
Partial refunds apply only where required by law. Enterprise contracts may override these defaults.

## 3. Shipping and Logistics

Standard shipping takes 5–7 business days. Express delivery arrives in 2 business days.
Tracking numbers are emailed after dispatch. Physical returns need the prepaid label within 14 days.

Warehouse processing happens on business days only. International customs delays are outside our SLA.
Damaged shipments require photos within 48 hours of delivery.

## 4. Security and Access

Reset passwords from the login page. Enable two-factor authentication for stronger security.
Locked accounts unlock after identity verification. Enterprise plans support SAML and OIDC SSO.

API keys must be rotated regularly. Never embed secret keys in mobile applications.
Sessions expire based on organization policy. Admins can revoke devices remotely.

## 5. Developer Platform

Free tier allows 60 requests per minute. Paid plans raise limits. HTTP 429 means back off and retry.
Check the Retry-After header. Semantic search ranks knowledge chunks by embedding similarity.

Create and rotate API keys in the developer dashboard. Use restricted keys for demos.
Webhooks retry with exponential backoff. Idempotency keys protect POST endpoints.

## 6. Privacy and Legal

Export or delete personal data from the privacy center. Support tickets are confidential.
Vectors of customer content are treated as sensitive as the source text.
Enterprise SLA targets 99.9% monthly uptime excluding planned maintenance.

Credits apply when availability falls below target after investigation.
Governing law is specified in the master service agreement.
"""


def sample_handbook() -> SourceDocument:
    return SourceDocument(
        id="doc-handbook",
        title="Acme Policy Handbook",
        text=POLICY_HANDBOOK.strip() + "\n",
        metadata={"source": "handbook", "version": "2026.1"},
    )


def sample_short() -> SourceDocument:
    return SourceDocument(
        id="doc-short",
        title="Short note",
        text="Alpha sentence one. Beta sentence two is different.\n\nGamma paragraph about refunds and money back.",
        metadata={"source": "note"},
    )
