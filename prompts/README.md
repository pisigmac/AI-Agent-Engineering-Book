# Master Prompts

Authoring automation prompts for the AI Agent Engineering Bootcamp.

| File | Role |
|------|------|
| `MASTER_BOOK_CREATION_PROMPT.md` | Chapter generation |
| `MASTER_REVIEW_PROMPT.md` | Chapter / code review |
| `MASTER_CODE_GENERATION_PROMPT.md` | Production code generation |
| `MASTER_PROJECT_MANAGER_PROMPT.md` | Roadmap, status, release planning |

These files are loaded by `scripts/lib/prompts.py` via `scripts/lib/paths.py`.

## Source-of-truth precedence (do not invert)

1. `BOOK_MANIFEST.md`
2. `BOOK_SPECIFICATION.md`
3. `BOOK_BIBLE.md`
4. `AI_ENGINEERING_PLAYBOOK.md`

Prompts operationalize those documents; they never override them.
