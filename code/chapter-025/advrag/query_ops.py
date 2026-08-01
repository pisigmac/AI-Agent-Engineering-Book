"""Multi-query generation and query expansion (rule-based offline)."""

from __future__ import annotations

import re

# Lightweight synonym / paraphrase expansions for support domain
_SYNONYMS: dict[str, list[str]] = {
    "refund": ["money back", "reverse charge", "chargeback"],
    "cancel": ["stop subscription", "turn off auto-renewal"],
    "password": ["login credentials", "account access", "reset credentials"],
    "shipping": ["delivery", "tracking number", "package"],
    "429": ["rate limit", "too many requests", "throttle"],
    "sso": ["single sign-on", "SAML", "OIDC"],
    "privacy": ["delete personal data", "export my data", "GDPR"],
}


def expand_query(query: str, *, max_expansions: int = 4) -> list[str]:
    """Return original query plus synonym expansions."""
    q = query.strip()
    out = [q]
    lower = q.lower()
    for key, alts in _SYNONYMS.items():
        if key in lower or any(a in lower for a in alts):
            for alt in alts:
                candidate = re.sub(re.escape(key), alt, q, flags=re.I) if key in lower else f"{q} {alt}"
                if candidate not in out:
                    out.append(candidate)
                if len(out) >= max_expansions + 1:
                    return out
    # generic paraphrase templates
    if len(out) == 1:
        out.append(f"explain {q}")
        out.append(f"how to {q}")
    return out[: max_expansions + 1]


def multi_queries(query: str, *, n: int = 3) -> list[str]:
    """Produce diverse reformulations for multi-query retrieval."""
    base = expand_query(query, max_expansions=max(0, n - 1))
    # ensure uniqueness and cap
    seen: list[str] = []
    for q in base:
        if q not in seen:
            seen.append(q)
        if len(seen) >= n:
            break
    while len(seen) < n:
        seen.append(f"{query} details")
        break
    return seen
