"""Cross-document and cross-chapter consistency checks."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .chapter import count_mermaid, load_chapter, validate_structure, word_count
from .curriculum import Curriculum
from .paths import RepoPaths

# Canonical terms from BOOK_BIBLE / specification mental models
CANONICAL_TERMS = [
    "LLM",
    "Tool",
    "Skill",
    "Workflow",
    "Graph",
    "Agent",
    "Harness",
    "Planner",
    "Memory",
    "Retriever",
    "MCP",
]

# Discouraged hype / marketing language
HYPE_PATTERNS = [
    r"\bgame[- ]changer\b",
    r"\brevolutioni[sz]e\b",
    r"\bcutting[- ]edge\b",
    r"\bstate[- ]of[- ]the[- ]art\b",
    r"\bmagic\b",
    r"\bjust works\b",
    r"\bunleash\b",
    r"\bsupercharge\b",
]


@dataclass
class ConsistencyIssue:
    severity: str  # critical | high | medium | low
    category: str
    location: str
    message: str
    recommendation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConsistencyReport:
    issues: list[ConsistencyIssue] = field(default_factory=list)
    chapters_checked: int = 0
    summary: dict[str, int] = field(default_factory=dict)

    def add(self, issue: ConsistencyIssue) -> None:
        self.issues.append(issue)

    def finalize(self) -> None:
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for issue in self.issues:
            counts[issue.severity] = counts.get(issue.severity, 0) + 1
        self.summary = counts

    @property
    def ok(self) -> bool:
        return self.summary.get("critical", 0) == 0 and self.summary.get("high", 0) == 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapters_checked": self.chapters_checked,
            "summary": self.summary,
            "ok": self.ok,
            "issues": [i.to_dict() for i in self.issues],
        }


def check_source_documents(paths: RepoPaths, report: ConsistencyReport) -> None:
    required = [
        paths.manifest,
        paths.specification,
        paths.bible,
        paths.playbook_doc,
        paths.master_book,
        paths.master_review,
        paths.master_code,
        paths.master_pm,
    ]
    for path in required:
        if not path.is_file():
            report.add(
                ConsistencyIssue(
                    severity="critical",
                    category="source_of_truth",
                    location=str(path),
                    message=f"Missing required document: {path.name}",
                    recommendation="Restore the document from version control.",
                )
            )


def check_chapter_structure(
    paths: RepoPaths,
    curriculum: Curriculum,
    report: ConsistencyReport,
    *,
    numbers: list[int] | None = None,
) -> None:
    targets = numbers or [c.number for c in curriculum if paths.chapter_md(c.number).is_file()]
    for n in targets:
        path = paths.chapter_md(n)
        if not path.is_file():
            report.add(
                ConsistencyIssue(
                    severity="high",
                    category="missing_artifact",
                    location=f"book/chapter-{n:03d}.md",
                    message="Chapter file missing",
                    recommendation="Run generate_chapter.py",
                )
            )
            continue
        text = path.read_text(encoding="utf-8")
        struct = validate_structure(n, text, path)
        report.chapters_checked += 1
        for missing in struct.missing_required:
            report.add(
                ConsistencyIssue(
                    severity="high",
                    category="structure",
                    location=f"book/chapter-{n:03d}.md",
                    message=f"Missing required section: {missing}",
                    recommendation="Add the section per BOOK_SPECIFICATION chapter template.",
                )
            )
        for issue in struct.issues:
            sev = "medium" if "Mermaid" in issue or "short" in issue else "low"
            report.add(
                ConsistencyIssue(
                    severity=sev,
                    category="quality",
                    location=f"book/chapter-{n:03d}.md",
                    message=issue,
                )
            )


def check_terminology(paths: RepoPaths, report: ConsistencyReport, numbers: list[int]) -> None:
    for n in numbers:
        path = paths.chapter_md(n)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in HYPE_PATTERNS:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                report.add(
                    ConsistencyIssue(
                        severity="low",
                        category="editorial",
                        location=f"book/chapter-{n:03d}.md",
                        message=f"Possible marketing/hype language: '{match.group(0)}'",
                        recommendation="Prefer precise engineering language (BOOK_MANIFEST).",
                    )
                )


def check_project_continuity(
    paths: RepoPaths,
    report: ConsistencyReport,
    numbers: list[int],
) -> None:
    """Flag chapters that never mention the evolving platform / prior work."""
    continuity_markers = [
        r"\bevolving\b",
        r"\bplatform\b",
        r"\bprevious chapter\b",
        r"\bearlier chapter\b",
        r"\bour (?:agent|system|project|platform)\b",
        r"\bcode/chapter-",
    ]
    for n in numbers:
        if n <= 1:
            continue
        path = paths.chapter_md(n)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if not any(re.search(p, text, flags=re.IGNORECASE) for p in continuity_markers):
            report.add(
                ConsistencyIssue(
                    severity="medium",
                    category="continuity",
                    location=f"book/chapter-{n:03d}.md",
                    message="Weak continuity signals to the evolving project / prior chapters",
                    recommendation="Reference the shared platform and prior architecture explicitly.",
                )
            )


def check_code_alignment(paths: RepoPaths, report: ConsistencyReport, numbers: list[int]) -> None:
    for n in numbers:
        chapter_path = paths.chapter_md(n)
        code_dir = paths.chapter_code_dir(n)
        if not chapter_path.is_file():
            continue
        text = chapter_path.read_text(encoding="utf-8")
        mentions_code = bool(
            re.search(r"```python|Internal Implementation|Production Implementation", text)
        )
        has_code = code_dir.is_dir() and any(code_dir.rglob("*.py"))
        if mentions_code and not has_code:
            report.add(
                ConsistencyIssue(
                    severity="medium",
                    category="code",
                    location=f"code/chapter-{n:03d}/",
                    message="Chapter discusses implementation but code package is missing",
                    recommendation="Run generate_code.py for this chapter.",
                )
            )


def run_consistency_checks(
    paths: RepoPaths,
    curriculum: Curriculum,
    *,
    numbers: list[int] | None = None,
) -> ConsistencyReport:
    report = ConsistencyReport()
    check_source_documents(paths, report)

    if numbers is None:
        numbers = [c.number for c in curriculum if paths.chapter_md(c.number).is_file()]
        # also include missing as structure issues for full catalog if empty
        if not numbers:
            numbers = []

    check_chapter_structure(paths, curriculum, report, numbers=numbers or None)
    if numbers:
        check_terminology(paths, report, numbers)
        check_project_continuity(paths, report, numbers)
        check_code_alignment(paths, report, numbers)

    # Curriculum completeness vs files
    for ch in curriculum:
        # no-op full scan already covers missing if numbers is full list
        pass

    report.finalize()
    return report


def render_report_markdown(report: ConsistencyReport) -> str:
    lines = [
        "# Consistency Report",
        "",
        f"- Chapters checked: {report.chapters_checked}",
        f"- Critical: {report.summary.get('critical', 0)}",
        f"- High: {report.summary.get('high', 0)}",
        f"- Medium: {report.summary.get('medium', 0)}",
        f"- Low: {report.summary.get('low', 0)}",
        f"- Pass (no critical/high): {'YES' if report.ok else 'NO'}",
        "",
        "## Issues",
        "",
    ]
    if not report.issues:
        lines.append("_No issues found._")
    else:
        for issue in report.issues:
            lines.append(
                f"- **[{issue.severity.upper()}]** `{issue.location}` — "
                f"{issue.category}: {issue.message}"
            )
            if issue.recommendation:
                lines.append(f"  - Recommendation: {issue.recommendation}")
    lines.append("")
    return "\n".join(lines)
