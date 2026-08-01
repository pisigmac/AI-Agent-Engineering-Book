"""Labeled retrieval pairs for embedding benchmarks (EN + multilingual)."""

from __future__ import annotations

from embbench.types import LabeledPair

# Shared corpus passages (document side)
CORPUS: dict[str, str] = {
    "refund": (
        "Refund policy: customers may reverse a charge or request money back within "
        "30 days of purchase for unused products."
    ),
    "shipping": (
        "Shipping: standard delivery takes 5-7 business days. Express arrives in 2 days. "
        "Tracking numbers are emailed after dispatch."
    ),
    "auth": (
        "Account security: reset your password from the login page and enable two-factor "
        "authentication. Locked accounts need identity verification."
    ),
    "api": (
        "API rate limits: free tier allows 60 requests per minute. HTTP 429 means back off "
        "and retry with exponential delay."
    ),
    "privacy": (
        "Privacy: export or delete personal data from the privacy center. Customer content "
        "and its vectors are confidential."
    ),
    "sso": (
        "Enterprise SSO: SAML and OIDC single sign-on map groups to roles. Session length "
        "is configurable per organization."
    ),
}


def english_pairs() -> list[LabeledPair]:
    return [
        LabeledPair("How do I get my money back?", "refund", ("shipping", "api", "auth"), tag="paraphrase"),
        LabeledPair("Where is my package tracking?", "shipping", ("refund", "privacy"), tag="paraphrase"),
        LabeledPair("I forgot my password", "auth", ("sso", "api"), tag="paraphrase"),
        LabeledPair("HTTP 429 too many requests", "api", ("refund", "shipping"), tag="keyword"),
        LabeledPair("Delete my personal data", "privacy", ("refund", "auth"), tag="paraphrase"),
        LabeledPair("Set up SAML for my company", "sso", ("auth", "api"), tag="paraphrase"),
        LabeledPair("reverse a charge unused product", "refund", ("shipping", "privacy"), tag="lexical"),
        LabeledPair("two-factor authentication login", "auth", ("sso", "privacy"), tag="lexical"),
    ]


def multilingual_pairs() -> list[LabeledPair]:
    """Non-English queries targeting English corpus (cross-lingual stress)."""
    return [
        LabeledPair(
            "¿Cómo solicito un reembolso?",
            "refund",
            ("shipping", "api"),
            lang="es",
            tag="es",
        ),
        LabeledPair(
            "Où est mon numéro de suivi colis?",
            "shipping",
            ("refund", "auth"),
            lang="fr",
            tag="fr",
        ),
        LabeledPair(
            "Ich habe mein Passwort vergessen",
            "auth",
            ("sso", "api"),
            lang="de",
            tag="de",
        ),
        LabeledPair(
            "limites de tasa API 429",
            "api",
            ("refund", "privacy"),
            lang="es",
            tag="es",
        ),
    ]


def all_pairs() -> list[LabeledPair]:
    return english_pairs() + multilingual_pairs()


def corpus_texts() -> dict[str, str]:
    return dict(CORPUS)
