# Changelog

All notable changes to this pack will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-04-21

### Added

Initial release of `langchain-py-pack`, the Python-native split of the
legacy `langchain-pack`. Targets LangChain 1.0.x + LangGraph 1.0.x (Oct 2025 release).

- **34 skills** organized into 6 tiers: Getting Started (S01-S04),
  Core Workflows (S05-S08), Operations (S09-S14), Pro (P15-P20),
  Flagship (F21-F24), and LangGraph v1.0 (L25-L34).
- **LangGraph v1.0 coverage** (missing from legacy pack):
  `StateGraph`, `create_react_agent`, `MemorySaver`/Postgres checkpointers,
  `interrupt_before`/`interrupt_after`, `stream_mode` modes (`messages`/`updates`/`values`),
  subgraphs, middleware, Deep Agents, native OTEL, typed content blocks.
- **docs/pain-catalog.md**: curated list of LangChain 1.0 / LangGraph 1.0
  pain points — each skill anchors to at least one entry.
- **Enterprise-grade SKILL.md quality bar**: every skill opens with a concrete
  failure mode (not capability prose), names ≥2 thresholds, cites ≥2 error
  codes or exceptions, includes a decision tree or comparison table, and
  ships 2-4 `references/*.md` mini-docs.
- **Version pinning**: every skill frontmatter carries `tested-against:
  langchain-core 1.0.x` so future readers can validate the baseline.

### Deprecated

- `plugins/saas-packs/langchain-pack` (legacy 24-skill pack) is superseded
  by `langchain-py-pack` + `langchain-ts-pack`. The legacy pack stays
  published for 90 days for back-compat. See its README for migration notes.
