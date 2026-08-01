# Chapter 54: Semantic Kernel

## Chapter Overview

Semantic Kernel-style kernel: plugins, planners, invoke pipeline.

Part VI compares **frameworks** after you built agents from first principles (Parts IV–V). This chapter teaches the **mental model and control surface** of Semantic Kernel via an offline adapter in `code/chapter-054/skernelx/` so you can map it onto your platform without treating the framework as architecture.

## Learning Objectives

- Explain core Semantic Kernel primitives
- Map them to harness/tools/memory/graph ports from earlier chapters
- Run the offline adapter tests
- Know when adopting Semantic Kernel helps vs hides critical control flow

## Prerequisites

- Parts IV–V (agents + systems engineering)
- Chapter 14 tools / 28 architecture / 39 harness

## Motivation

Frameworks accelerate demos—and can erase budgets, authz, and eval if used as a black box. Learn the shape, then wrap it.

## First Principles

### 1. Frameworks are adapters, not your domain model
### 2. Keep budgets, authz, and traces outside the vendor object graph
### 3. Prefer typed tools and explicit state
### 4. Prove behavior with offline tests before live keys

## Core Theory

See package docstrings and `main.py` for the canonical object graph of this framework family.

## Architecture

```text
code/chapter-054/skernelx/runtime.py
```

## Internal Implementation

```bash
cd code/chapter-054 && pytest -q && python3 main.py
```

## Production Implementation

- Install the real SDK when you adopt it
- Inject your tool registry, memory, and harness
- Add eval + observability from Part V

## Trade-offs

| Use framework | Build yourself |
|---|---|
| Speed, ecosystem | Control, fewer surprises |

## Debugging

Map framework traces back to your step IDs and tool names.

## Security

Never grant frameworks ambient credentials; pass scoped tools only.

## Best Practices

1. Thin adapter layer  
2. Shared tool schemas  
3. External eval suite  
4. Explicit termination  

## Mini Project

Offline **Semantic Kernel** adapter demonstrating the framework’s primary runtime loop.

## Visual diagrams

![Lifecycle](../diagrams/png/chapter-054/lifecycle.png)

![Overview](../diagrams/png/chapter-054/overview.png)


## Chapter Deliverables

| Artifact | Location |
|---|---|
| Manuscript | `book/chapter-054.md` |
| Package | `code/chapter-054/skernelx/` |

## Chapter Summary

Semantic Kernel-style kernel: plugins, planners, invoke pipeline.

## What's Next

**Chapter 55** continues Part VI.