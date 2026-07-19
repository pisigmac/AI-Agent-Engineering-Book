# AI Platform — Git & GitHub Workflow

Team rules for the AI Agent Engineering Bootcamp monorepo.

## Branching

- Default branch: `main` (always releasable)
- Create short-lived branches:

```text
feat/<slug>
fix/<slug>
docs/<slug>
chore/<slug>
test/<slug>
ci/<slug>
refactor/<slug>
perf/<slug>
release/<version>
```

Examples:

- `feat/chapter-004-git-toolkit`
- `fix/tool-http-timeout`
- `docs/chapter-002-harness`

## Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
type(scope): subject
```

Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`.

Validate before commit:

```bash
cd code/chapter-004
python main.py check-commit "feat(chapter-004): add inventory"
python main.py check-branch
```

## Pull requests

Every PR includes:

1. Summary (what/why)
2. Stack layers touched (from Chapter 2 vocabulary)
3. Risk (security, cost, data, compatibility)
4. Test plan + commands run
5. Eval impact
6. Rollback notes

Keep PRs small and single-intent.

## CI expectations

Before merge:

- `pytest` for affected `code/chapter-*/` packages
- No secrets in diff
- Manuscript structure checks when `book/` changes (optional via `scripts/check_consistency.py`)

## Never commit

- `.env`, API keys, tokens
- `.venv/`, `__pycache__/`, caches
- Large datasets/model weights
- Unredacted production transcripts

## Inventory

Summarize blast radius of a branch:

```bash
python main.py inventory --base main
```

If `source_of_truth` docs change, require elevated review.
