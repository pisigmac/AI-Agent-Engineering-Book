# Chapter 70: Skill Registry

## Chapter Overview

Part VIII module **Skill Registry** (`fwskills`) — a composable piece of the in-house agent framework.

## Learning Objectives

- Use and extend the `fwskills` module
- Test it offline
- Wire it into the harness/loop later chapters assemble

## Prerequisites

Parts IV–VII; earlier Part VIII modules.

## Motivation

Own skill registry so product code does not depend on a single vendor abstraction.

## Architecture

`code/chapter-070/fwskills/`

## Internal Implementation

```bash
cd code/chapter-070 && pytest -q && python3 main.py
```

## Production Implementation

Replace mocks with real backends; keep interfaces stable.

## Mini Project

Skill Registry framework module.

## Visual diagrams

![Lifecycle](../diagrams/png/chapter-070/lifecycle.png)

![Overview](../diagrams/png/chapter-070/overview.png)


## Chapter Deliverables

| Artifact | Location |
|---|---|
| Manuscript | `book/chapter-070.md` |
| Package | `code/chapter-070/fwskills/` |

## Chapter Summary

Skill Registry implemented as a first-class framework component.

## What's Next

**Chapter 71** continues Part VIII.
