"""Static prompt tests for CI gates."""

from __future__ import annotations

from dataclasses import dataclass

from promptlib.registry import PromptRegistry
from promptlib.template import collect_required_vars, render_prompt
from promptlib.types import PromptSpec


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    message: str


@dataclass(frozen=True)
class SuiteReport:
    passed: bool
    results: list[CheckResult]

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "results": [r.__dict__ for r in self.results],
        }


class PromptTestSuite:
    def __init__(self, registry: PromptRegistry) -> None:
        self.registry = registry

    def run(self) -> SuiteReport:
        results: list[CheckResult] = []
        for row in self.registry.list():
            spec = self.registry.get(row["id"], row["version"])
            results.extend(self._check_spec(spec))
        passed = all(r.ok for r in results)
        return SuiteReport(passed=passed, results=results)

    def _check_spec(self, spec: PromptSpec) -> list[CheckResult]:
        out: list[CheckResult] = []
        prefix = f"{spec.id}@{spec.version}"

        out.append(
            CheckResult(
                f"{prefix}:system_or_user",
                bool(spec.system.strip() or spec.user_template.strip()),
                "must define system or user_template",
            )
        )

        if spec.risk == "high":
            out.append(
                CheckResult(
                    f"{prefix}:high_risk_constraints",
                    len(spec.constraints) > 0,
                    "high-risk prompts require constraints",
                )
            )

        # Render with placeholders for required vars
        vars_needed = collect_required_vars(spec)
        sample_vars = {k: f"<{k}>" for k in vars_needed}
        try:
            rendered = render_prompt(spec, sample_vars)
            out.append(
                CheckResult(
                    f"{prefix}:renderable",
                    len(rendered.messages) > 0,
                    "render produced messages",
                )
            )
            roles = [m.role for m in rendered.messages]
            out.append(
                CheckResult(
                    f"{prefix}:has_system_for_policy",
                    "system" in roles or spec.risk != "high",
                    "high-risk prompts should render a system message",
                )
            )
        except Exception as exc:  # noqa: BLE001
            out.append(CheckResult(f"{prefix}:renderable", False, str(exc)))

        banned = ("ignore previous instructions", "ignore all prior")
        blob = "\n".join(
            [spec.system, spec.developer, spec.user_template]
            + [ex.user + "\n" + ex.assistant for ex in spec.examples]
        ).lower()
        hit = next((b for b in banned if b in blob), None)
        out.append(
            CheckResult(
                f"{prefix}:no_injection_fewshots",
                hit is None,
                f"contains banned phrase: {hit}" if hit else "ok",
            )
        )

        if spec.max_tokens_est is not None:
            # rough char heuristic for static ceiling
            size = len(blob) // 4
            ok = size <= spec.max_tokens_est
            out.append(
                CheckResult(
                    f"{prefix}:token_ceiling",
                    ok,
                    (
                        f"approx tokens {size} within max_tokens_est {spec.max_tokens_est}"
                        if ok
                        else f"approx tokens {size} exceeds max_tokens_est {spec.max_tokens_est}"
                    ),
                )
            )

        return out
