# Chapter 26: Hybrid Search

## Chapter Overview

Chapter 25 introduced hybrid retrieval inside an advanced RAG stack. This chapter isolates **hybrid search** as its own engineering discipline: BM25, dense embeddings, explicit sparse TF-IDF vectors, fusion (RRF and weighted), and labeled evaluation so you can prove which channel wins on which queries.

**Project:** a production-shaped `hybridret` package with mode comparison and eval harness.

## Learning Objectives

After completing this chapter, you can:

- Implement BM25, dense, and sparse TF-IDF retrievers
- Fuse ranked lists with RRF and weighted normalized scores
- Evaluate Recall@k and MRR across modes on a labeled set
- Explain when keywords beat embeddings (and vice versa)
- Ship a hybrid retriever CLI for search and benchmarks

## Prerequisites

- Chapters 18–25 (semantic search, embeddings, advanced RAG)
- Basic IR metrics

## Motivation

Dense-only systems miss exact error codes (`E-4032`). BM25-only systems miss “money back” ↔ “refund”. Hybrid search is how production search teams stop choosing one failure mode.

## First Principles

### 1. Channels fail differently
### 2. Fusion needs rank agreement more than raw score calibration (RRF)
### 3. Evaluate with labels, not vibes
### 4. Keep modes toggleable for incident response
### 5. Sparse is not only BM25 — TF-IDF vectors are also sparse signals

## Mental Model

```mermaid
flowchart TB
  Q[Query] --> BM25
  Q --> Dense
  Q --> Sparse[Sparse TF-IDF]
  BM25 --> Fuse[RRF / weighted]
  Dense --> Fuse
  Sparse --> Fuse
  Fuse --> Hits[Top-k]
  Hits --> Eval[Recall@k / MRR]
```

## Core Theory

**BM25** — lexical probabilistic ranking.  
**Dense** — embedding cosine (offline hash stand-in here).  
**Sparse TF-IDF** — explicit high-dim sparse vectors.  
**RRF** — `sum 1/(k+rank)` across lists.  
**Weighted fusion** — min-max normalize per channel then weight.

## Architecture

```text
code/chapter-026/hybridret/
  bm25.py dense.py sparse.py fusion.py eval.py retriever.py corpus.py
```

## Internal Implementation

```bash
python main.py search "E-4032" --mode bm25
python main.py compare "money back"
python main.py eval
```

## Production Implementation

- OpenSearch/Elastic BM25 + FAISS/pgvector dense
- Learned sparse (SPLADE) optional third channel
- Online/offline eval dashboards; per-query channel attribution

## Framework Implementation

LangChain ensemble retrievers map to your fusion layer—own the metrics.

## Trade-offs

| Mode | Strength | Weakness |
|---|---|---|
| BM25 | Exact tokens | Paraphrase |
| Dense | Meaning | Codes/IDs |
| Hybrid | Balanced | Dual index ops |

## Debugging

| Symptom | Check |
|---|---|
| Misses SKUs | BM25 weight / tokenization |
| Misses paraphrase | Dense quality / fusion |
| Eval flat | Label noise; k too small |

## Performance

Candidate_k then fuse; cache embeddings; parallel channel search.

## Security

Same ACL filters on every channel before fusion.

## Best Practices

1. Always keep a labeled set  
2. Log which channels contributed  
3. Prefer RRF as default fusion  
4. Re-eval after corpus or model changes  
5. Don’t drop BM25 for “semantic only” marketing

## Anti-Patterns

| Anti-pattern | Failure |
|---|---|
| Dense-only forever | Exact-match misses |
| Uncalibrated score sum | Dominated channel |
| No eval | Silent regressions |

## Hands-on Exercise

1. Compare modes on `E-4032` vs `money back`.  
2. Run `eval` and note hybrid_rrf vs bm25.  
3. Tune weighted fusion and re-eval.

## Mini Project

**Hybrid retriever** with multi-mode search and evaluation.

## Visual diagrams

![Eval Loop](../diagrams/png/chapter-026/eval-loop.png)

![Hybrid Channels](../diagrams/png/chapter-026/hybrid-channels.png)


## Chapter Deliverables

| Artifact | Location |
|---|---|
| Manuscript | `book/chapter-026.md` |
| Package | `code/chapter-026/hybridret/` |
| Tests | `code/chapter-026/tests/` |

## Interview Questions

1. Why hybrid search?  
2. RRF vs weighted fusion?  
3. When does BM25 beat dense?  
4. How do you evaluate fusion?  
5. Operational cost of dual indexes?

## Quiz

1. RRF uses: **ranks not raw scores**  
2. Error codes often need: **lexical/BM25**  
3. Hybrid default goal: **higher robust recall**

## Cheat Sheet

```bash
cd code/chapter-026 && pytest -q && python3 main.py eval
```

## Chapter Summary

Hybrid search combines lexical and dense (and optional sparse vector) channels with principled fusion and labeled evaluation—so retrieval quality is engineered, not guessed.

## What's Next

**Part VI — Frameworks** maps these primitives onto OpenAI Agents SDK, LangGraph, CrewAI, AutoGen, PydanticAI, Semantic Kernel, and Google ADK.
