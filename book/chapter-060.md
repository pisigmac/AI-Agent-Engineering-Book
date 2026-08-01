# Chapter 60: Redis

## Chapter Overview

Production engineering for the AI agent platform: **Redis**. This chapter provides an offline-testable package that models the production control surface so you can integrate real infrastructure without losing architecture discipline.

## Learning Objectives

- Apply Redis patterns to agent systems
- Run the chapter package tests and CLI
- Know failure modes and operational defaults

## Prerequisites

- Parts IV–VI
- Prior Part VII chapters

## Motivation

Agents that only work in notebooks are not products. Redis is how they become operable services.

## First Principles

### 1. Explicit interfaces over ambient infrastructure
### 2. Fail closed on auth, budgets, and deploys
### 3. Everything emits logs/metrics/traces
### 4. Test the control plane without live cloud accounts

## Architecture

```text
code/chapter-060/
```

## Internal Implementation

```bash
cd code/chapter-060 && pytest -q && python3 main.py
```

## Production Implementation

Swap offline fakes for managed services while keeping the same contracts and tests as behavioral specs.

## Best Practices

1. Infrastructure as code  
2. Secrets outside images  
3. Health checks and rollbacks  
4. Correlation IDs end-to-end  

## Mini Project

Redis control-plane package for the platform.

## Visual diagrams

![Lifecycle](../diagrams/png/chapter-060/lifecycle.png)

![Overview](../diagrams/png/chapter-060/overview.png)


## Chapter Deliverables

| Artifact | Location |
|---|---|
| Manuscript | `book/chapter-060.md` |
| Code | `code/chapter-060/` |

## Chapter Summary

Redis as a production building block for the agent platform.

## What's Next

**Chapter 61** continues Part VII.
