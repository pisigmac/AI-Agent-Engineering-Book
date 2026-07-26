"""Knowledge-base corpus for the semantic search engine mini project."""

from __future__ import annotations

from searchkit.types import Document, LabeledQuery


def knowledge_base() -> list[Document]:
    return [
        Document(
            id="kb-refund",
            title="Refund policy",
            text=(
                "Customers may request a refund or reverse a charge within 30 days "
                "of purchase for unused products. Chargebacks follow the same window. "
                "Contact billing to start a money-back request."
            ),
            metadata={"topic": "billing", "product": "core", "lang": "en"},
        ),
        Document(
            id="kb-cancel",
            title="Cancel subscription",
            text=(
                "Stop auto-renewal in account settings at any time. Access continues "
                "until the end of the paid period. Partial-period refunds only where required by law."
            ),
            metadata={"topic": "billing", "product": "core", "lang": "en"},
        ),
        Document(
            id="kb-shipping",
            title="Shipping and delivery",
            text=(
                "Standard shipping takes 5–7 business days. Express delivery arrives in "
                "2 business days. Tracking numbers are emailed after the package ships."
            ),
            metadata={"topic": "logistics", "product": "retail", "lang": "en"},
        ),
        Document(
            id="kb-returns",
            title="Physical returns",
            text=(
                "Return physical goods within 14 days of delivery using the prepaid label. "
                "Items must be unused and in original packaging. Refunds post after warehouse scan."
            ),
            metadata={"topic": "logistics", "product": "retail", "lang": "en"},
        ),
        Document(
            id="kb-auth",
            title="Password and 2FA",
            text=(
                "Reset your password from the login page. Enable two-factor authentication "
                "for stronger security. Locked accounts unlock after identity verification."
            ),
            metadata={"topic": "security", "product": "core", "lang": "en"},
        ),
        Document(
            id="kb-sso",
            title="Single sign-on",
            text=(
                "Enterprise plans support SAML and OIDC single sign-on. Map groups to roles "
                "in the admin console. Session length is configurable per organization."
            ),
            metadata={"topic": "security", "product": "enterprise", "lang": "en"},
        ),
        Document(
            id="kb-api-limits",
            title="API rate limits",
            text=(
                "Free tier allows 60 requests per minute. Paid plans raise limits. "
                "HTTP 429 means back off and retry with exponential delay. Check the Retry-After header."
            ),
            metadata={"topic": "developers", "product": "api", "lang": "en"},
        ),
        Document(
            id="kb-api-keys",
            title="API keys",
            text=(
                "Create and rotate API keys in the developer dashboard. Never embed secret keys "
                "in mobile apps. Use restricted keys for client-side demos."
            ),
            metadata={"topic": "developers", "product": "api", "lang": "en"},
        ),
        Document(
            id="kb-privacy",
            title="Privacy and data export",
            text=(
                "Export or delete personal data from the privacy center. Support tickets are "
                "confidential. Vectors of customer content are treated as sensitive as the source text."
            ),
            metadata={"topic": "legal", "product": "core", "lang": "en"},
        ),
        Document(
            id="kb-sla",
            title="Service level agreement",
            text=(
                "Enterprise SLA targets 99.9% monthly uptime excluding planned maintenance. "
                "Credits apply when availability falls below the target after investigation."
            ),
            metadata={"topic": "legal", "product": "enterprise", "lang": "en"},
        ),
        Document(
            id="kb-rag",
            title="How retrieval works",
            text=(
                "Semantic search ranks knowledge chunks by embedding similarity. Top results "
                "are packed into the model context as untrusted evidence for grounded answers."
            ),
            metadata={"topic": "developers", "product": "api", "lang": "en"},
        ),
        Document(
            id="kb-pricing",
            title="Plan pricing overview",
            text=(
                "Starter is free with limited API calls. Pro adds higher rate limits and SSO add-on. "
                "Enterprise includes custom contracts, SLA, and dedicated support."
            ),
            metadata={"topic": "billing", "product": "core", "lang": "en"},
        ),
    ]


def labeled_queries() -> list[LabeledQuery]:
    return [
        LabeledQuery("How do I get my money back?", ("kb-refund",), "refund paraphrase"),
        LabeledQuery("Where is my package tracking number?", ("kb-shipping",), "shipping"),
        LabeledQuery("I forgot my password", ("kb-auth",), "auth"),
        LabeledQuery("HTTP 429 rate limit", ("kb-api-limits",), "api limits"),
        LabeledQuery("Set up SAML SSO for my company", ("kb-sso",), "enterprise sso"),
        LabeledQuery("Delete my personal data", ("kb-privacy",), "privacy"),
        LabeledQuery("What is the uptime SLA credit?", ("kb-sla",), "sla"),
        LabeledQuery("How does semantic retrieval ground answers?", ("kb-rag",), "rag"),
    ]
