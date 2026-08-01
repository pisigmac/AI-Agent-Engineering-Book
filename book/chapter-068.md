# Chapter 68: Prompt Manager

## Chapter Overview

Part VIII builds **your own AI agent framework**. This chapter implements **Prompt Manager** as a production-minded, offline-testable module under `code/chapter-068/promptmgr/`.

These modules compose into a coherent platform: client → prompts → tools/skills → plan/loop → memory/workflow/graph → reflection → schedule/harness → evaluate → plugins.

## Learning Objectives

- Implement the Prompt Manager module with clear interfaces
- Test behavior without live network dependencies
- Integrate it with adjacent framework modules

## Prerequisites

- Parts IV–VII
- Prior Part VIII chapters

## Motivation

Frameworks hide control flow. Building Prompt Manager yourself means you can replace vendor pieces without rewriting product logic.

## First Principles

### 1. Stable interfaces beat framework fashion
### 2. Budgets, authz, and traces are non-negotiable
### 3. Offline tests define the contract
### 4. Compose modules; do not monorepo-spaghetti

## Architecture

```text
code/chapter-068/promptmgr/
```

## Internal Implementation

```bash
cd code/chapter-068 && pytest -q && python3 main.py
```

## Production Implementation

Swap mock LLM/backends for real providers; keep the same types and error model.

## Best Practices

1. Typed inputs/outputs  
2. Explicit failure codes  
3. Versioned configs  
4. Trace hooks  

## Mini Project

**Prompt Manager** framework module.

## Visual diagrams

![Lifecycle](../diagrams/png/chapter-068/lifecycle.png)

![Overview](../diagrams/png/chapter-068/overview.png)


## Chapter Deliverables

| Artifact | Location |
|---|---|
| Manuscript | `book/chapter-068.md` |
| Package | `code/chapter-068/promptmgr/` |

## Chapter Summary

Prompt Manager as a first-class framework building block.

## What's Next

**Chapter 69** continues Part VIII.
