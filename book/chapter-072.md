# Chapter 72: Execution Loop

## Chapter Overview

Part VIII module **Execution Loop** (`fwloop`) — a composable piece of the in-house agent framework.

## Learning Objectives

- Use and extend the `fwloop` module
- Test it offline
- Wire it into the harness/loop later chapters assemble

## Prerequisites

Parts IV–VII; earlier Part VIII modules.

## Motivation

Own execution loop so product code does not depend on a single vendor abstraction.

## Architecture

`code/chapter-072/fwloop/`

## Internal Implementation

```bash
cd code/chapter-072 && pytest -q && python3 main.py
```

## Production Implementation

Replace mocks with real backends; keep interfaces stable.

## Mini Project

Execution Loop framework module.

## Visual diagrams

![Lifecycle](../diagrams/png/chapter-072/lifecycle.png)

![Overview](../diagrams/png/chapter-072/overview.png)


## Chapter Deliverables

| Artifact | Location |
|---|---|
| Manuscript | `book/chapter-072.md` |
| Package | `code/chapter-072/fwloop/` |

## Chapter Summary

Execution Loop implemented as a first-class framework component.

## What's Next

**Chapter 73** continues Part VIII.
