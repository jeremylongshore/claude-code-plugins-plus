# Upstream reference

This skill is a marketplace-tier adapter for the upstream skill at
https://github.com/mturac/recsys-pipeline-architect (v0.1.0, MIT).

For full content, load the upstream reference documents as needed:

| Topic | Upstream file |
|-------|---------------|
| Pipeline interfaces in 4 languages (TypeScript, Go, Python, Rust) | [`references/interfaces.md`](https://github.com/mturac/recsys-pipeline-architect/blob/main/references/interfaces.md) |
| Multi-action prediction pattern (when, how, weight tuning) | [`references/multi-action-scoring.md`](https://github.com/mturac/recsys-pipeline-architect/blob/main/references/multi-action-scoring.md) |
| Candidate isolation via attention masking, cacheability argument | [`references/candidate-isolation.md`](https://github.com/mturac/recsys-pipeline-architect/blob/main/references/candidate-isolation.md) |
| 12 common filters with implementation sketches | [`references/filter-cookbook.md`](https://github.com/mturac/recsys-pipeline-architect/blob/main/references/filter-cookbook.md) |
| Scoring patterns: weighted sum, diversity penalty, MMR, position debiasing | [`references/scorer-cookbook.md`](https://github.com/mturac/recsys-pipeline-architect/blob/main/references/scorer-cookbook.md) |

## Runnable example scaffolds

| Stack | Path | Test suite |
|-------|------|------------|
| Strapi v5 plugin (TypeScript) | [`examples/strapi-content-feed/`](https://github.com/mturac/recsys-pipeline-architect/tree/main/examples/strapi-content-feed) | Jest (3/3 pass) |
| Zentra-compatible pipeline (Go, generics) | [`examples/zentra-go/`](https://github.com/mturac/recsys-pipeline-architect/tree/main/examples/zentra-go) | go test (3/3 pass) |
| PMAI task prioritizer (Python, FastAPI) | [`examples/pmai-task-prioritizer/`](https://github.com/mturac/recsys-pipeline-architect/tree/main/examples/pmai-task-prioritizer) | pytest (3/3 pass) |

## Pattern attribution

The six-stage pipeline (Source → Hydrator → Filter → Scorer → Selector →
SideEffect), multi-action scoring approach, and candidate isolation rule are
inspired by xAI's open-sourced X For You algorithm: https://github.com/xai-org/x-algorithm
(Apache 2.0). This skill is an independent reimplementation of the pattern
under MIT. No source code is copied from the original.
