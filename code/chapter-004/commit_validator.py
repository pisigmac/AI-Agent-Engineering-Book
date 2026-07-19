"""Validate conventional commit messages."""

from __future__ import annotations

from git_policy import COMMIT_RE, CONVENTIONAL_TYPES, ValidationResult


def validate_commit_message(message: str) -> ValidationResult:
    lines = [ln.rstrip() for ln in message.strip().splitlines()]
    if not lines or not lines[0].strip():
        return ValidationResult(False, errors=("empty commit message",))

    header = lines[0].strip()
    errors: list[str] = []
    warnings: list[str] = []

    if len(header) > 72:
        warnings.append(f"header is {len(header)} chars; prefer ≤72")

    match = COMMIT_RE.match(header)
    if not match:
        errors.append(
            "header must match: type(scope)?: subject — "
            f"allowed types: {', '.join(CONVENTIONAL_TYPES)}"
        )
        return ValidationResult(False, errors=tuple(errors), warnings=tuple(warnings))

    subject = match.group("subject").strip()
    if not subject:
        errors.append("subject must not be empty")
    elif subject.endswith("."):
        warnings.append("prefer subject without trailing period")
    if subject and subject[0].isupper():
        warnings.append("prefer lower-case subject start (conventional style)")
    if subject and (
        subject.lower().startswith("wip")
        or subject.lower() in {"fix", "updates", "changes", "stuff"}
    ):
        errors.append("subject is too vague for production history")

    if len(lines) > 1 and lines[1].strip() != "":
        errors.append("blank line required between header and body")

    return ValidationResult(not errors, errors=tuple(errors), warnings=tuple(warnings))
