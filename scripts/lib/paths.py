"""Canonical repository paths for the book project."""

from __future__ import annotations

from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Walk upward until BOOK_MANIFEST.md is found."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "BOOK_MANIFEST.md").is_file():
            return candidate
    # Fallback: scripts/ is two levels below repo when installed as scripts/lib/
    script_root = Path(__file__).resolve().parents[2]
    if (script_root / "BOOK_MANIFEST.md").is_file():
        return script_root
    raise FileNotFoundError(
        "Could not locate repository root (BOOK_MANIFEST.md not found). "
        "Run scripts from inside the AI-Agent-Engineering-Bootcamp repo."
    )


class RepoPaths:
    """Resolved paths for all project artifacts."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or find_repo_root()
        self.book = self.root / "book"
        self.code = self.root / "code"
        self.diagrams = self.root / "diagrams"
        self.diagrams_mermaid = self.diagrams / "mermaid"
        self.diagrams_drawio = self.diagrams / "drawio"
        self.diagrams_png = self.diagrams / "png"
        self.playbook = self.root / "playbook"
        self.assets = self.root / "assets"
        self.prompts = self.root / "prompts"
        self.scripts = self.root / "scripts"
        self.scripts_data = self.scripts / "data"
        self.reviews = self.root / "reviews"
        self.releases = self.root / "releases"
        self.build = self.root / "build"
        self.reports = self.root / "reports"
        self.state = self.root / ".book_state"
        self.config_file = self.root / "scripts" / "config.yaml"
        self.curriculum_file = self.scripts_data / "curriculum.yaml"

        # Source-of-truth documents (priority order)
        self.manifest = self.root / "BOOK_MANIFEST.md"
        self.specification = self.root / "BOOK_SPECIFICATION.md"
        self.bible = self.root / "BOOK_BIBLE.md"
        self.playbook_doc = self.root / "AI_ENGINEERING_PLAYBOOK.md"

        self.master_book = self.prompts / "MASTER_BOOK_CREATION_PROMPT.md"
        self.master_review = self.prompts / "MASTER_REVIEW_PROMPT.md"
        self.master_code = self.prompts / "MASTER_CODE_GENERATION_PROMPT.md"
        self.master_pm = self.prompts / "MASTER_PROJECT_MANAGER_PROMPT.md"

    def ensure_layout(self) -> None:
        """Create expected directories if missing."""
        for path in (
            self.book,
            self.code,
            self.diagrams,
            self.diagrams_mermaid,
            self.diagrams_drawio,
            self.diagrams_png,
            self.playbook,
            self.assets,
            self.prompts,
            self.reviews,
            self.releases,
            self.build,
            self.reports,
            self.state,
        ):
            path.mkdir(parents=True, exist_ok=True)

    def chapter_md(self, number: int) -> Path:
        return self.book / f"chapter-{number:03d}.md"

    def chapter_code_dir(self, number: int) -> Path:
        return self.code / f"chapter-{number:03d}"

    def chapter_diagram_dir(self, number: int) -> Path:
        return self.diagrams_mermaid / f"chapter-{number:03d}"

    def chapter_review(self, number: int) -> Path:
        return self.reviews / f"chapter-{number:03d}-review.md"

    def relative(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.root))
        except ValueError:
            return str(path)
