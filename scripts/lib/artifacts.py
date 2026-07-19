"""Parse multi-file LLM outputs and write repository artifacts safely."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .paths import RepoPaths

# ```path:code/chapter-001/main.py
# or ```python path=code/...
_PATH_FENCE = re.compile(
    r"```(?:path:|(?:python|py|toml|yml|yaml|md|json|txt|dockerfile|sh|bash)?\s*(?:path=)?)"
    r"([^\n`]+)\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)

_SIMPLE_FENCE = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)


@dataclass
class FileArtifact:
    relative_path: str
    content: str


def parse_path_fenced_files(text: str) -> list[FileArtifact]:
    """Extract files marked with path: or path= fences."""
    artifacts: list[FileArtifact] = []
    for match in _PATH_FENCE.finditer(text):
        rel = match.group(1).strip().strip("`").strip()
        # Clean common prefixes from language tags mixed in
        rel = re.sub(r"^(python|py|toml|yml|yaml|md|json|txt|dockerfile|sh|bash)\s+", "", rel)
        rel = rel.replace("path=", "").strip()
        if not rel or "/" not in rel and not rel.endswith((".py", ".md", ".toml", ".yml", ".yaml", ".txt", ".json")):
            continue
        content = match.group(2)
        if not content.endswith("\n"):
            content += "\n"
        artifacts.append(FileArtifact(relative_path=rel.lstrip("./"), content=content))
    return artifacts


def write_artifacts(
    paths: RepoPaths,
    artifacts: list[FileArtifact],
    *,
    allowed_prefixes: tuple[str, ...] = ("code/", "diagrams/", "book/", "playbook/"),
    force: bool = False,
) -> list[Path]:
    written: list[Path] = []
    for art in artifacts:
        rel = art.relative_path.replace("\\", "/")
        if ".." in Path(rel).parts:
            raise ValueError(f"Refusing path traversal: {rel}")
        if not any(rel.startswith(p) for p in allowed_prefixes):
            # Allow chapter-relative paths by prefixing code/ if bare
            if rel.startswith("chapter-"):
                rel = f"code/{rel}"
            else:
                raise ValueError(
                    f"Artifact path not under allowed prefixes {allowed_prefixes}: {rel}"
                )
        dest = paths.root / rel
        if dest.exists() and not force:
            raise FileExistsError(f"Refusing to overwrite existing file without --force: {dest}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(art.content, encoding="utf-8")
        written.append(dest)
    return written


def extract_mermaid_blocks(text: str) -> list[tuple[str, str]]:
    """Return list of (slug_hint, mermaid_source)."""
    blocks: list[tuple[str, str]] = []
    pattern = re.compile(
        r"(?:###\s*Diagram:\s*([^\n]+)\n+)?```mermaid\s*\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    for idx, match in enumerate(pattern.finditer(text), start=1):
        slug = (match.group(1) or f"diagram-{idx}").strip()
        slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", slug).strip("-").lower() or f"diagram-{idx}"
        source = match.group(2).strip() + "\n"
        blocks.append((slug, source))
    return blocks


def write_mermaid_diagrams(
    paths: RepoPaths,
    chapter_number: int,
    blocks: list[tuple[str, str]],
    *,
    force: bool = False,
) -> list[Path]:
    out_dir = paths.chapter_diagram_dir(chapter_number)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for slug, source in blocks:
        dest = out_dir / f"{slug}.mmd"
        if dest.exists() and not force:
            # unique-ify
            dest = out_dir / f"{slug}-{len(written)+1}.mmd"
        dest.write_text(source, encoding="utf-8")
        written.append(dest)
    return written
