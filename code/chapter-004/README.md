# Chapter 004 — Git & GitHub Toolkit

Lightweight workflow tooling for conventional commits, branch names, and monorepo change inventory.

## Setup

```bash
cd code/chapter-004
pip install pytest
```

## Commands

```bash
python main.py check-commit "feat(chapter-004): add commit validator"
python main.py check-branch feat/git-toolkit
python main.py inventory --base main
pytest -q
```

## Layout

| File | Role |
|------|------|
| `git_policy.py` | Shared regex/policy |
| `commit_validator.py` | Conventional commit checks |
| `branch_validator.py` | Branch naming checks |
| `change_inventory.py` | Path → area/chapter map |
| `main.py` | CLI |
| `WORKFLOW.md` | Team workflow standard |
| `tests/` | Unit tests |

## See also

- Chapter manuscript: `book/chapter-004.md`
- Team workflow: `WORKFLOW.md`
