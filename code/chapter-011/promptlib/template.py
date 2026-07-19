"""Template rendering with {{var}} placeholders and validation."""

from __future__ import annotations

import re
from typing import Mapping

from promptlib.types import ChatMessage, FewShotExample, PromptSpec, RenderedPrompt

_VAR = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")


class TemplateError(ValueError):
    pass


def find_vars(text: str) -> set[str]:
    return set(_VAR.findall(text or ""))


def render_string(template: str, variables: Mapping[str, str]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise TemplateError(f"missing template variable: {key}")
        return str(variables[key])

    return _VAR.sub(repl, template)


def collect_required_vars(spec: PromptSpec) -> set[str]:
    found: set[str] = set()
    for block in (spec.system, spec.developer, spec.user_template):
        found |= find_vars(block)
    for ex in spec.examples:
        found |= find_vars(ex.user) | find_vars(ex.assistant)
    if spec.required_vars:
        found |= set(spec.required_vars)
    return found


def render_prompt(spec: PromptSpec, variables: Mapping[str, str] | None = None) -> RenderedPrompt:
    variables = {k: str(v) for k, v in dict(variables or {}).items()}
    required = collect_required_vars(spec)
    missing = sorted(required - set(variables))
    if missing:
        raise TemplateError(f"missing required variables: {', '.join(missing)}")

    messages: list[ChatMessage] = []

    system_body = render_string(spec.system, variables).strip() if spec.system else ""
    if spec.constraints:
        constraint_block = "Constraints:\n" + "\n".join(f"- {c}" for c in spec.constraints)
        system_body = (system_body + "\n\n" + constraint_block).strip()
    if system_body:
        messages.append(ChatMessage(role="system", content=system_body))

    if spec.developer.strip():
        messages.append(
            ChatMessage(role="system", content=render_string(spec.developer, variables).strip())
        )

    for ex in spec.examples:
        messages.append(ChatMessage(role="user", content=render_string(ex.user, variables).strip()))
        messages.append(
            ChatMessage(role="assistant", content=render_string(ex.assistant, variables).strip())
        )

    if spec.user_template.strip():
        messages.append(
            ChatMessage(role="user", content=render_string(spec.user_template, variables).strip())
        )

    if not messages:
        raise TemplateError("render produced no messages")

    return RenderedPrompt(
        prompt_id=spec.id,
        version=spec.version,
        messages=tuple(messages),
        variables=variables,
        metadata={"tags": list(spec.tags), "risk": spec.risk},
    )


def build_zero_shot(
    *,
    system: str,
    user: str,
    constraints: list[str] | None = None,
) -> list[ChatMessage]:
    spec = PromptSpec(
        id="ad_hoc.zero_shot",
        version="0.0.0",
        system=system,
        user_template=user,
        constraints=tuple(constraints or ()),
    )
    return list(render_prompt(spec, {}).messages)


def build_few_shot(
    *,
    system: str,
    examples: list[FewShotExample],
    user: str,
    constraints: list[str] | None = None,
) -> list[ChatMessage]:
    spec = PromptSpec(
        id="ad_hoc.few_shot",
        version="0.0.0",
        system=system,
        user_template=user,
        constraints=tuple(constraints or ()),
        examples=tuple(examples),
    )
    return list(render_prompt(spec, {}).messages)
