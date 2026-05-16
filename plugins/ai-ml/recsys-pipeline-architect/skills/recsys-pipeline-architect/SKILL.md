---
name: recsys-pipeline-architect
description: |
  Designs composable recommendation, ranking, and feed pipelines using the six-stage
  Source→Hydrator→Filter→Scorer→Selector→SideEffect framework popularized by xAI's
  open-sourced For You algorithm. Use when the user wants to build any system that
  picks "the top K items for a (user, context)" — content feeds, search ranking,
  task prioritization, notification ordering, RAG retrieval ranking, alert triage,
  ad selection. Trigger with "recommendation system", "feed algorithm", "ranking
  pipeline", "for you feed", "how should I rank X", "candidate pipeline",
  "content recommender", "pipeline architecture for recsys", "RAG retrieval reranker".
allowed-tools: Read, Write
version: 1.0.0
author: Mehmet Turac <noreply@github.com>
license: MIT
compatibility: Designed for Claude Code, also compatible with Codex, Cursor, Gemini CLI, and any agentskills.io-compatible agent
tags:
- ai
- ml
- recommendation-system
- ranking
- feed-algorithm
- personalization
- pipeline-architecture
- rag-reranker
user-invocable: true
---

# recsys-pipeline-architect

A spec-and-scaffold skill for building composable recommendation, ranking, and feed pipelines using the six-stage **Source → Hydrator → Filter → Scorer → Selector → SideEffect** framework.

## Overview

Most "recommendation systems" in production are not exotic ML — they are *pipelines*: fetch candidates from one or more sources, enrich them with metadata, filter the ineligible, score the rest, sort, pick the top K, and fire off side effects. The pattern is universal. The implementation language and the scoring function change; the pipeline shape does not.

This skill encodes that pattern as six composable stages (popularized by xAI's open-sourced [X For You algorithm](https://github.com/xai-org/x-algorithm), Apache 2.0 — this skill is MIT and is an independent reimplementation of the pattern), gives the user the trade-offs at each stage (multi-action vs single-score, candidate isolation vs joint scoring, online vs offline batch), and produces a runnable scaffold in the user's stack.

## Prerequisites

- Familiarity with the user's target runtime (Node/TypeScript, Go, Python, or another language)
- Ability to express the use case as "given (user, context), return top K items"
- A scoring function (ML model, heuristic, or LLM-as-judge) — the skill plumbs the pipeline around it but does not produce the scoring function itself

No external services or environment variables are required.

## Instructions

When invoked, walk the user through eight steps:

1. **Clarify the use case** (one round, ask only what is missing):
   - What are the items being ranked? (posts, products, tasks, alerts, documents)
   - What is the input context? (user ID, search query, current document, time window)
   - What language / runtime? (TypeScript/Node, Go, Python, Rust)

2. **Identify the candidate sources.** Most pipelines have at least two: in-network (followed/owned/subscribed/recent) and out-of-network (ML retrieval, trending, similar-to-liked). Single-source is also valid.

3. **List the required hydrations.** For each filter and scorer the user might want, what data does it need that the source did not provide? Each missing piece is a hydrator. Common: core metadata, author/owner profile, subscription/permission status, engagement counters, freshness/age. Use `Read` to inspect existing schema/types if the user points at a repo.

4. **List the filters.** Order matters — cheap before expensive, universal before user-specific. Common: duplicate, self, age, block/mute, previously-served, eligibility (paywall, geo-restriction, permission).

5. **Design the scorer chain.** Primary ML/heuristic scorer → combiner (weighted sum if multi-action) → diversity reranking → business-rule scorer (boosts/penalties).

6. **Selector.** Almost always: sort descending by final score, take top K. Variations: stratified selection (mix in-network and out-of-network at fixed ratio), positional debiasing.

7. **SideEffects.** Things that must happen after the response is sent, never blocking it: cache served IDs, emit impression events, update counters, log for analytics. Always fire-and-forget.

8. **Generate the scaffold.** Use `Write` to emit the pipeline interface definitions in the user's language, a minimal runnable example, and a README explaining how to add new stages.

### Architectural trade-offs to surface (do not default silently)

- **Single score vs multi-action prediction.** Single score = retrain to change behavior. Multi-action = predict `P(action)` for many actions, combine with weights at serving time. Recommend multi-action when the user expects to tune frequently.
- **Candidate isolation vs joint scoring.** Isolated = deterministic, cacheable. Joint = more expressive, harder to cache. Default to isolation.
- **Online vs offline batch.** Request-time = 100–300ms latency, fresh. Offline = lower latency, lower freshness. Hybrid = candidate retrieval offline, ranking online.

## Output

For each step, produce:

- A markdown summary of the decision and the chosen trade-off
- For step 8, a directory tree of the scaffold (interfaces + runnable example + README)

The final scaffold is a working starter — not pseudocode. If the scaffold needs dependencies, install instructions are part of the output.

## Error Handling

- **User describes a problem outside the "top K for (user, context)" shape** (e.g., regression model, classification only, generative task) → stop, suggest a different framing or skill.
- **User asks for benchmark numbers** ("how fast is this?", "how much memory does it use?") → respond "depends on workload, run it yourself" — do not fabricate latency or throughput claims.
- **User wants to brand their artifact "X-like" or use "For You" naming** → push back. The pattern is free to use; the brand is not. Suggest neutral naming: "candidate pipeline", "feed pipeline", "ranking pipeline", "recsys pipeline".
- **Generated scaffold fails to run** → debug and re-emit. No "this should work in theory" delivery — the scaffold must actually execute.
- **User's stack is unsupported** → fall back to the language-agnostic interface definitions in the upstream `references/interfaces.md` (TypeScript, Go, Python, Rust) and adapt manually.

## Examples

**Example 1: Strapi content feed**

User: "I'm running a Strapi v5 instance with 50k articles. I want a 'for you' feed personalized to each logged-in user based on their reading history."

Walk through the 8 steps and generate a Strapi plugin scaffold with multi-action scoring (`P(read)`, `P(like)`, `P(share)`, `P(skip)`), author diversity, standard filters, and an async side-effect lane.

**Example 2: RAG retrieval reranker**

User: "My RAG returns top-50 chunks from a vector DB. I want to rerank them with a more expensive scorer and return top-5."

Single-source pipeline with a scorer chain (cheap retrieval + expensive rerank). Two-stage. Generate a Python async pipeline using the upstream `examples/pmai-task-prioritizer/` as a template.

**Example 3: Notification triage**

User: "We send too many notifications. I want a daily digest that picks the top 10 from the last 24h queue."

Offline-batch pipeline. Source = queue. Filters = age, deduplication, eligibility. Scorer = urgency × user-affinity. Selector = top 10. Side effect = email send (still async, even in batch).

**Example 4: Task prioritizer**

User: "PMAI receives a queue of incoming task suggestions. I want to rank them by 'what should this user work on next' considering their past patterns."

Items reversed (tasks instead of content). Same six-stage shape applies. Generate FastAPI scaffold.

## Resources

- **Upstream repository:** https://github.com/mturac/recsys-pipeline-architect
- **Release:** v0.1.0
- **Full SKILL.md:** [upstream SKILL.md](https://github.com/mturac/recsys-pipeline-architect/blob/main/SKILL.md)
- **Reference docs (load on demand):**
  - [interfaces in 4 languages](https://github.com/mturac/recsys-pipeline-architect/blob/main/references/interfaces.md)
  - [multi-action scoring](https://github.com/mturac/recsys-pipeline-architect/blob/main/references/multi-action-scoring.md)
  - [candidate isolation](https://github.com/mturac/recsys-pipeline-architect/blob/main/references/candidate-isolation.md)
  - [filter cookbook (12 patterns)](https://github.com/mturac/recsys-pipeline-architect/blob/main/references/filter-cookbook.md)
  - [scorer cookbook](https://github.com/mturac/recsys-pipeline-architect/blob/main/references/scorer-cookbook.md)
- **Runnable example scaffolds (all green on tests):**
  - [examples/strapi-content-feed/](https://github.com/mturac/recsys-pipeline-architect/tree/main/examples/strapi-content-feed) (TypeScript / Jest)
  - [examples/zentra-go/](https://github.com/mturac/recsys-pipeline-architect/tree/main/examples/zentra-go) (Go with generics)
  - [examples/pmai-task-prioritizer/](https://github.com/mturac/recsys-pipeline-architect/tree/main/examples/pmai-task-prioritizer) (Python / FastAPI / pytest)
- **Pattern source:** [xai-org/x-algorithm](https://github.com/xai-org/x-algorithm) (Apache 2.0)
- **Install via skills.sh (one-liner, 17+ agents):** `npx skills add mturac/recsys-pipeline-architect`
