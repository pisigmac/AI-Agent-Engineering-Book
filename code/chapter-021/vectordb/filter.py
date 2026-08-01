"""Metadata filter evaluation for pre/post vector search."""

from __future__ import annotations

from typing import Any


def matches(metadata: dict[str, Any], filt: dict[str, Any] | None) -> bool:
    """Mongo-ish subset of operators.

    Equality: ``{"topic": "billing"}``
    Operators: ``{"score": {"$gte": 1}}``, ``{"topic": {"$in": ["a","b"]}}``,
    ``{"$and": [...]}``, ``{"$or": [...]}``.
    """
    if not filt:
        return True
    if "$and" in filt:
        return all(matches(metadata, sub) for sub in filt["$and"])
    if "$or" in filt:
        return any(matches(metadata, sub) for sub in filt["$or"])

    for key, expected in filt.items():
        if key.startswith("$"):
            continue
        actual = metadata.get(key)
        if isinstance(expected, dict) and any(k.startswith("$") for k in expected):
            if not _ops(actual, expected):
                return False
        else:
            if actual != expected:
                return False
    return True


def _ops(actual: Any, ops: dict[str, Any]) -> bool:
    if "$eq" in ops and actual != ops["$eq"]:
        return False
    if "$ne" in ops and actual == ops["$ne"]:
        return False
    if "$in" in ops and actual not in ops["$in"]:
        return False
    if "$nin" in ops and actual in ops["$nin"]:
        return False
    if "$gt" in ops and not (actual is not None and actual > ops["$gt"]):
        return False
    if "$gte" in ops and not (actual is not None and actual >= ops["$gte"]):
        return False
    if "$lt" in ops and not (actual is not None and actual < ops["$lt"]):
        return False
    if "$lte" in ops and not (actual is not None and actual <= ops["$lte"]):
        return False
    if "$exists" in ops:
        exists = actual is not None
        if bool(ops["$exists"]) != exists:
            return False
    return True
