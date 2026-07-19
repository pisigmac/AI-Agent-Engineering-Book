"""Filesystem-backed versioned prompt registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from promptlib.template import TemplateError, render_prompt
from promptlib.types import FewShotExample, PromptSpec, RenderedPrompt


class RegistryError(KeyError):
    pass


def _parse_spec(data: dict[str, Any]) -> PromptSpec:
    examples = tuple(
        FewShotExample(user=ex["user"], assistant=ex["assistant"])
        for ex in data.get("examples") or []
    )
    return PromptSpec(
        id=str(data["id"]),
        version=str(data["version"]),
        description=str(data.get("description") or ""),
        system=str(data.get("system") or ""),
        developer=str(data.get("developer") or ""),
        user_template=str(data.get("user_template") or ""),
        constraints=tuple(data.get("constraints") or ()),
        examples=examples,
        required_vars=tuple(data.get("required_vars") or ()),
        tags=tuple(data.get("tags") or ()),
        risk=str(data.get("risk") or "normal"),
        max_tokens_est=data.get("max_tokens_est"),
        metadata=dict(data.get("metadata") or {}),
    )


class PromptRegistry:
    def __init__(self) -> None:
        self._specs: dict[tuple[str, str], PromptSpec] = {}
        self._latest: dict[str, str] = {}

    @classmethod
    def from_directory(cls, path: Path | str) -> "PromptRegistry":
        reg = cls()
        root = Path(path)
        if not root.is_dir():
            raise FileNotFoundError(f"prompt library not found: {root}")
        for file in sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml")):
            data = yaml.safe_load(file.read_text(encoding="utf-8")) or {}
            if not isinstance(data, dict):
                raise ValueError(f"invalid prompt file: {file}")
            reg.register(_parse_spec(data))
        return reg

    def register(self, spec: PromptSpec) -> None:
        key = (spec.id, spec.version)
        self._specs[key] = spec
        prev = self._latest.get(spec.id)
        if prev is None or _version_key(spec.version) >= _version_key(prev):
            self._latest[spec.id] = spec.version

    def get(self, prompt_id: str, version: str | None = None) -> PromptSpec:
        ver = version or self._latest.get(prompt_id)
        if ver is None:
            raise RegistryError(f"unknown prompt id: {prompt_id}")
        try:
            return self._specs[(prompt_id, ver)]
        except KeyError as exc:
            raise RegistryError(f"unknown prompt {prompt_id}@{ver}") from exc

    def list(self) -> list[dict[str, str]]:
        rows = []
        for prompt_id, version in sorted(self._latest.items()):
            spec = self.get(prompt_id, version)
            rows.append(
                {
                    "id": prompt_id,
                    "version": version,
                    "risk": spec.risk,
                    "description": spec.description,
                }
            )
        return rows

    def render(
        self,
        prompt_id: str,
        variables: Mapping[str, str] | None = None,
        *,
        version: str | None = None,
    ) -> RenderedPrompt:
        spec = self.get(prompt_id, version=version)
        return render_prompt(spec, variables)


def _version_key(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for p in version.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def default_library_path() -> Path:
    return Path(__file__).resolve().parent / "library"
