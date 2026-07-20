# Diagrams

| Path | Contents |
|------|----------|
| `mermaid/chapter-XXX/` | Mermaid **source** (edit these) |
| `png/chapter-XXX/` | **Rendered PNG** images for the book |
| `mermaid/platform/` | Cross-chapter workflow diagrams |
| `png/platform/` | Rendered platform workflows |
| `drawio/` | Optional draw.io sources |

## Render PNGs

```bash
# requires Node.js
npm install --no-fund @mermaid-js/mermaid-cli puppeteer
./scripts/render_diagrams.sh
python3 scripts/embed_diagram_images.py
```

Chapters include a **Visual diagrams** section that embeds the PNGs so GitHub and PDF/export pipelines show images even when Mermaid fences are not rendered.

## Naming

```text
diagrams/mermaid/chapter-012/context-pipeline.mmd
  → diagrams/png/chapter-012/context-pipeline.png
  → book embed: ../diagrams/png/chapter-012/context-pipeline.png
```
