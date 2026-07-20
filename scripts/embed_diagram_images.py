#!/usr/bin/env python3
"""Insert PNG image embeds into chapter markdown for each rendered diagram.

Idempotent: skips images already referenced in the chapter.
Adds a '## Visual diagrams' section before Chapter Deliverables (or at end).
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "book"
PNG_ROOT = ROOT / "diagrams" / "png"


def chapter_num(path: Path) -> int | None:
    m = re.match(r"chapter-(\d+)\.md$", path.name)
    return int(m.group(1)) if m else None


def title_from_stem(stem: str) -> str:
    return stem.replace("-", " ").replace("_", " ").strip().title()


def ensure_visual_section(md_path: Path, pngs: list[Path]) -> bool:
    text = md_path.read_text(encoding="utf-8")
    rel_prefix = "../diagrams/png"
    chapter = f"chapter-{chapter_num(md_path):03d}"
    lines_to_add: list[str] = []
    for png in sorted(pngs):
        rel = f"{rel_prefix}/{chapter}/{png.name}"
        if rel in text or png.name in text:
            continue
        lines_to_add.append(f"![{title_from_stem(png.stem)}]({rel})")
        lines_to_add.append("")
    if not lines_to_add:
        return False

    section = ["## Visual diagrams", ""] + lines_to_add
    section_text = "\n".join(section)

    if "## Visual diagrams" in text:
        # Replace existing section body until next ##
        text2 = re.sub(
            r"## Visual diagrams\n(?:.*?)(?=\n## |\Z)",
            section_text + "\n",
            text,
            count=1,
            flags=re.DOTALL,
        )
        md_path.write_text(text2, encoding="utf-8")
        return True

    anchor = "## Chapter Deliverables"
    if anchor in text:
        text2 = text.replace(anchor, section_text + "\n" + anchor, 1)
    else:
        text2 = text.rstrip() + "\n\n" + section_text + "\n"
    md_path.write_text(text2, encoding="utf-8")
    return True


def main() -> int:
    changed = 0
    for md in sorted(BOOK.glob("chapter-*.md")):
        n = chapter_num(md)
        if n is None:
            continue
        png_dir = PNG_ROOT / f"chapter-{n:03d}"
        if not png_dir.is_dir():
            continue
        pngs = list(png_dir.glob("*.png"))
        if not pngs:
            continue
        if ensure_visual_section(md, pngs):
            print(f"updated {md.name} ({len(pngs)} images)")
            changed += 1
        else:
            print(f"ok      {md.name} (already embedded)")
    print(f"chapters_updated={changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
