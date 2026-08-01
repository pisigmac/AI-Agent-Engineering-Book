# Chapter 31: Tool Calling

## Chapter Overview

Tool manager with schema validation, permissions, sandbox flags.

This chapter is part of **Part IV — Agent Engineering**. It extends the evolving agent platform with production-minded interfaces and offline-testable implementations.

## Learning Objectives

After completing this chapter, you can:

- Tools vs skills
- Permission gates
- Validate before execute
- Run the chapter project and interpret its structured output
- Place the component in the larger agent runtime

## Prerequisites

- Chapters 1–26 foundations (especially tools, structured outputs, RAG where relevant)
- Prior Part IV chapters through 30

## Motivation

Agents fail in production when autonomy is unbounded, tools are ungoverned, or state is implicit. This chapter makes **tool calling** an explicit, testable subsystem.

## First Principles

### 1. Tools vs skills

### 2. Permission gates

### 3. Validate before execute


## Mental Model

See Visual diagrams for the component flow.

## Core Theory

The implementation encodes the theory as typed interfaces and a CLI-runnable project. Prefer explicit state transitions, budgets, and structured results over free-text control flow.

## Architecture

```text
code/chapter-031/toolmgr/
  tests/
  main.py
```

## Internal Implementation

Run the package CLI/tests under `code/chapter-031/`. Key entrypoints live in the `toolmgr` package.

## Production Implementation

- Replace offline policies/mocks with real model calls behind the same interfaces
- Add authz, audit logs, and metrics around every side effect
- Persist state where the component owns long-lived data
- Enforce step/time/cost budgets at the harness boundary

## Framework Implementation

LangGraph, CrewAI, AutoGen, and SDKs should map onto these ports—not replace your domain model.

## Trade-offs

| Approach | Pros | Cons |
|---|---|---|
| Explicit component | Testable, swappable | More boilerplate |
| Framework magic | Fast demos | Hidden control flow |

## Debugging

| Symptom | Check |
|---|---|
| Non-termination | Missing terminate condition / max steps |
| Silent tool failure | Validation and error mapping |
| Bad multi-step quality | Memory and observation formatting |

## Performance

Bound steps, cache pure tools, parallelize only independent work.

## Security

Least-privilege tools, sandbox high-risk actions, treat observations as untrusted.

## Best Practices

1. Typed inputs/outputs
2. Budgets on loops
3. Structured traces
4. Tests without network
5. Clear ownership of state

## Anti-Patterns

| Anti-pattern | Failure |
|---|---|
| Unbounded autonomy | Cost and safety incidents |
| Stringly-typed tools | Runtime chaos |
| No traces | Un-debuggable agents |

## Hands-on Exercise

1. Run the chapter tests.
2. Execute the CLI demo.
3. Modify one policy/handler and re-test.
4. Note how the component would plug into Chapter 28’s skeleton / later harnesses.

## Mini Project

**Tool registry / manager**

## Visual diagrams

![Lifecycle](../diagrams/png/chapter-031/lifecycle.png)

![Overview](../diagrams/png/chapter-031/overview.png)


## Chapter Deliverables

| Artifact | Location |
|---|---|
| Manuscript | `book/chapter-031.md` |
| Package | `code/chapter-031/toolmgr/` |
| Tests | `code/chapter-031/tests/` |
| Diagrams | `diagrams/mermaid|png/chapter-031/` |

## Interview Questions

1. What problem does this component solve in an agent system?
2. What are its inputs, outputs, and failure modes?
3. How do budgets/permissions apply?
4. How would you test it without live models?
5. How does it interact with tools and memory?

## Quiz

1. Part IV focuses on: **agent engineering building blocks**
2. Side effects should go through: **validated tools/executors**
3. Loops need: **explicit termination and budgets**

## Cheat Sheet

```bash
cd code/chapter-031 && pytest -q && python3 main.py --help || python3 main.py
```

## Chapter Summary

Tool manager with schema validation, permissions, sandbox flags. Deliverable: **Permission-safe execution**.

## What's Next

**Chapter 32** continues Part IV.