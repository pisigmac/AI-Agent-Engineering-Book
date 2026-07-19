"""Validate branch names for short-lived workflow."""

from __future__ import annotations

from git_policy import BRANCH_RE, ValidationResult


def validate_branch_name(name: str) -> ValidationResult:
    name = name.strip()
    if not name:
        return ValidationResult(False, errors=("empty branch name",))
    if name.startswith("origin/"):
        name = name[len("origin/") :]
    if not BRANCH_RE.match(name):
        return ValidationResult(
            False,
            errors=(
                "branch must be main/develop or "
                "{feat|fix|docs|chore|test|refactor|ci|perf|release}/slug",
            ),
        )
    if len(name) > 80:
        return ValidationResult(False, errors=("branch name too long (>80)",))
    return ValidationResult(True)
