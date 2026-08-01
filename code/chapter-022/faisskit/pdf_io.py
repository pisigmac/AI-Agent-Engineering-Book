"""Minimal PDF write/read for demos (no pypdf dependency).

Writes simple Latin-text one-or-more page PDFs and extracts text via a
lightweight parser for the files we generate. Production: use pypdf/pdfminer.
"""

from __future__ import annotations

import re
from pathlib import Path


def write_text_pdf(path: str | Path, pages: list[str], *, title: str = "Document") -> Path:
    """Write a minimal multi-page PDF with one text block per page."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    objects: list[bytes] = []
    # 1: Catalog, 2: Pages, then page objs, content objs, font

    def enc(s: str) -> bytes:
        # Escape PDF string specials
        s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        return s.encode("latin-1", errors="replace")

    font_obj_num = 3
    page_objs: list[int] = []
    content_objs: list[int] = []

    # We'll assign numbers after building body parts carefully.
    # Structure:
    # 1 catalog
    # 2 pages
    # 3 font
    # then pairs of page/content for each page

    kids = []
    body_parts: list[tuple[int, bytes]] = []

    next_num = 4
    for page_text in pages:
        # simple layout: Helvetica 11, start near top
        lines = page_text.splitlines() or [""]
        # limit lines for demo
        lines = lines[:40]
        y = 760
        tj_ops = []
        for line in lines:
            safe = line[:90]
            tj_ops.append(f"BT /F1 11 Tf 50 {y} Td ({_pdf_escape(safe)}) Tj ET")
            y -= 14
            if y < 50:
                break
        stream = "\n".join(tj_ops).encode("latin-1", errors="replace")
        content_num = next_num
        page_num = next_num + 1
        next_num += 2
        content_objs.append(content_num)
        page_objs.append(page_num)
        kids.append(page_num)

        content = (
            f"{content_num} 0 obj\n"
            f"<< /Length {len(stream)} >>\n"
            f"stream\n".encode()
            + stream
            + b"\nendstream\nendobj\n"
        )
        page = (
            f"{page_num} 0 obj\n"
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {content_num} 0 R /Resources << /Font << /F1 3 0 R >> >> >>\n"
            f"endobj\n"
        ).encode()
        body_parts.append((content_num, content))
        body_parts.append((page_num, page))

    font = b"3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    kids_str = " ".join(f"{k} 0 R" for k in kids)
    pages_obj = (
        f"2 0 obj\n<< /Type /Pages /Kids [{kids_str}] /Count {len(kids)} >>\nendobj\n"
    ).encode()
    catalog = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"

    # Assemble in object number order
    ordered: dict[int, bytes] = {
        1: catalog,
        2: pages_obj,
        3: font,
    }
    for num, blob in body_parts:
        ordered[num] = blob

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = {0: 0}
    for i in range(1, max(ordered) + 1):
        offsets[i] = len(out)
        out.extend(ordered[i])

    xref_pos = len(out)
    n_obj = max(ordered)
    out.extend(f"xref\n0 {n_obj + 1}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for i in range(1, n_obj + 1):
        out.extend(f"{offsets[i]:010d} 00000 n \n".encode())
    out.extend(
        f"trailer\n<< /Size {n_obj + 1} /Root 1 0 R /Info << /Title ({_pdf_escape(title)}) >> >>\n".encode()
    )
    out.extend(b"startxref\n")
    out.extend(f"{xref_pos}\n".encode())
    out.extend(b"%%EOF\n")
    path.write_bytes(bytes(out))
    return path


def _pdf_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def extract_text(path: str | Path) -> list[str]:
    """Extract text strings from a simple PDF (Tj operands).

    Returns one string per page when page breaks are detectable; otherwise
    a single joined page.
    """
    raw = Path(path).read_bytes()
    # Split by page content streams roughly via 'BT' blocks grouping
    # Find all Tj strings: (text) Tj
    parts = re.findall(rb"\((?:\\.|[^\\()])*\)\s*Tj", raw)
    texts: list[str] = []
    for p in parts:
        m = re.match(rb"\((.*)\)\s*Tj", p, re.S)
        if not m:
            continue
        s = m.group(1)
        s = s.replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\")
        texts.append(s.decode("latin-1", errors="replace"))
    if not texts:
        return [""]
    # Group into pages by re-parsing content streams
    streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", raw, re.S)
    if streams:
        pages = []
        for st in streams:
            line_parts = re.findall(rb"\((?:\\.|[^\\()])*\)\s*Tj", st)
            lines = []
            for p in line_parts:
                m = re.match(rb"\((.*)\)\s*Tj", p, re.S)
                if not m:
                    continue
                s = m.group(1).replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\")
                lines.append(s.decode("latin-1", errors="replace"))
            if lines:
                pages.append("\n".join(lines))
        if pages:
            return pages
    return ["\n".join(texts)]
