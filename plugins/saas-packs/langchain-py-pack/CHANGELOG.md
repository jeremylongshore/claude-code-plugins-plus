# Changelog

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned (next epics)

- **A2** — Getting Started + Core Workflows: `langchain-install-auth`,
  `langchain-hello-world`, `langchain-common-errors`, `langchain-sdk-patterns`,
  `langchain-core-workflow`, `langchain-data-handling` (6 full-quality skills)
- **A3** — Operations + Pro: 12 skills covering observability, incident
  response, prod checklist, CI / deploy, performance / cost / rate limits,
  security, RBAC, multi-env
- **A4** — Flagship + LangGraph v1.0: 14 skills covering reference
  architecture, webhooks, local-dev loop, upgrade migration, and the full
  LangGraph v1.0 surface (StateGraph, agents, checkpointing, HITL, streaming,
  subgraphs, middleware, Deep Agents, OTEL, content blocks)

Each epic ships as one PR. Every skill follows the same gold-standard quality
bar as the two v2.0.0 skills: concrete pain in the Overview, 2+ error codes
named, 2-4 references, decision trees / comparison tables where applicable,
and every code block pinned to LangChain 1.0.x.

## [2.0.0] - 2026-04-21

### Added

Initial release of `langchain-py-pack`, the Python-native split of the legacy
`langchain-pack`. Targets LangChain 1.0.x + LangGraph 1.0.x (Oct 2025 release).

- `langchain-model-inference` — full skill (200+ lines) covering `ChatAnthropic`,
  `ChatOpenAI`, `ChatGoogleGenerativeAI` initialization, content-block
  iteration, streaming token accounting, and structured-output method decision
  tree. Ships with 4 reference files: `content-blocks`, `token-accounting`,
  `structured-output-methods`, `provider-quirks`.
- `langchain-embeddings-search` — full skill (220+ lines) covering FAISS vs
  Pinecone flipped score semantics, embedding-dim mismatch prevention,
  language-aware chunking, hybrid BM25 + vector, and rerankers. Ships with 3
  reference files: `vector-store-comparison`, `score-semantics`, `hybrid-search`.
- `docs/pain-catalog.md` — 68-entry catalog of LangChain 1.0 / LangGraph 1.0
  pain points spanning 23 categories (model inference, LCEL, agents, vector
  stores, LangGraph state, memory, middleware, observability, rate limits,
  security, deployment, migration, streaming, and more). Every entry names a
  concrete symptom, the root cause, the fix headline, and the skills it anchors.
- Pack scaffold: plugin.json (v2.0.0), scoped npm package.json
  (`@intentsolutionsio/langchain-py-pack`), LICENSE (MIT), CHANGELOG, and a
  README that covers what is shipped today plus the explicit four-epic roadmap
  for the remaining 32 skills.

### Deprecated

- `plugins/saas-packs/langchain-pack` (legacy 24-skill pack) is superseded by
  `langchain-py-pack` + `langchain-ts-pack` (the TypeScript counterpart lands
  in Epic B). The legacy pack stays published for 90 days for back-compat.
  Full deprecation banner, CLI notice, and blog post ship in Epic C1.
