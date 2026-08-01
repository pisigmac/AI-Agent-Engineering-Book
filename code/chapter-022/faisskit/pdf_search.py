"""PDF search project: extract → chunk → FAISS index → query."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from faisskit.pdf_io import extract_text, write_text_pdf
from faisskit.service import FaissIndexService


def chunk_pages(
    pages: list[str],
    *,
    source: str,
    max_chars: int = 400,
) -> list[dict[str, Any]]:
    """Split each page into character windows for indexing."""
    docs: list[dict[str, Any]] = []
    for pi, page in enumerate(pages):
        text = page.strip()
        if not text:
            continue
        if len(text) <= max_chars:
            docs.append(
                {
                    "id": f"{source}::p{pi:03d}::c000",
                    "text": text,
                    "metadata": {"source": source, "page": pi, "chunk": 0},
                }
            )
            continue
        step = max(1, max_chars - 40)
        ci = 0
        for start in range(0, len(text), step):
            piece = text[start : start + max_chars]
            if not piece.strip():
                continue
            docs.append(
                {
                    "id": f"{source}::p{pi:03d}::c{ci:03d}",
                    "text": piece,
                    "metadata": {"source": source, "page": pi, "chunk": ci},
                }
            )
            ci += 1
            if start + max_chars >= len(text):
                break
    return docs


@dataclass
class PdfSearchEngine:
    service: FaissIndexService
    sources: list[str]

    @classmethod
    def from_pdfs(
        cls,
        paths: list[str | Path],
        *,
        kind: str = "flat_ip",
        dimensions: int = 64,
        max_chars: int = 400,
    ) -> PdfSearchEngine:
        svc = FaissIndexService(kind=kind, dimensions=dimensions, nlist=8, nprobe=2)
        sources: list[str] = []
        all_docs: list[dict[str, Any]] = []
        for path in paths:
            path = Path(path)
            sources.append(path.name)
            pages = extract_text(path)
            all_docs.extend(chunk_pages(pages, source=path.name, max_chars=max_chars))
        if all_docs:
            svc.add_documents(all_docs)
        return cls(service=svc, sources=sources)

    def search(self, query: str, *, k: int = 5, source: str | None = None):
        where = {"source": source} if source else None
        return self.service.search(query, k=k, where=where)


def build_sample_pdfs(directory: str | Path) -> list[Path]:
    """Create two small policy PDFs for the chapter project."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    refund = write_text_pdf(
        directory / "refund_policy.pdf",
        [
            "Acme Refund Policy\n\n"
            "Customers may request a refund or reverse a charge within 30 days\n"
            "of purchase if the product is unused. Contact billing for money back.",
            "Chargebacks follow the same window. Subscriptions cancel in settings\n"
            "and continue until the paid period ends.",
        ],
        title="Refund Policy",
    )
    shipping = write_text_pdf(
        directory / "shipping_guide.pdf",
        [
            "Acme Shipping Guide\n\n"
            "Standard shipping takes 5 to 7 business days. Express delivery arrives\n"
            "in 2 business days. Tracking numbers are emailed after dispatch.",
            "Returns need the prepaid label within 14 days of delivery.\n"
            "Warehouse processing happens on business days only.",
        ],
        title="Shipping Guide",
    )
    security = write_text_pdf(
        directory / "security_faq.pdf",
        [
            "Security FAQ\n\n"
            "Reset your password from the login page. Enable two-factor authentication.\n"
            "Enterprise plans support SAML and OIDC single sign-on.",
            "API rate limits: free tier allows 60 requests per minute.\n"
            "HTTP 429 means back off and retry with exponential delay.",
        ],
        title="Security FAQ",
    )
    return [refund, shipping, security]
