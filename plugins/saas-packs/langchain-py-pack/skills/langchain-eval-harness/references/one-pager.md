# langchain-eval-harness — One-Pager

Build reproducible evaluation pipelines for LangChain 1.0 chains and LangGraph 1.0 agents — golden sets, LangSmith `evaluate()`, ragas, deepeval, trajectory analysis, and CI regression gates.

## The Problem

Most LLM chains and agents ship without measurement. A team swaps `gpt-4o` for `claude-sonnet-4-6` to save money; a week later CS notices answers dropped on 15% of tickets — the regression was invisible in code review and CI because no one had a golden set. LangSmith, ragas, and deepeval all exist, but the patterns for wiring them into a loop with statistical significance, version tags, and PR-blocking thresholds are scattered across five doc sites.

## The Solution

This skill gives you a 100-example golden-set format (JSONL + version tag), a `langsmith.evaluate()` wiring pattern with a custom evaluator, a ragas RAG quartet (faithfulness, answer relevance, context precision/recall) wired through `RagasEvaluator`, a deepeval LLM-as-judge with run-level quorum for judge disagreement, a LangGraph trajectory evaluator that scores tool-call sequences with partial credit, and a GitHub Actions workflow that gates PRs on a 2% mean drop or 5% per-example drop — with bootstrap CI and paired Wilcoxon significance. Pinned to `langchain-core 1.0.x`, `langsmith>=0.2`, `ragas>=0.2`, `deepeval>=2.0`.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Researchers, PhDs, ML engineers, senior backend — anyone shipping LLM systems who needs reproducible measurement |
| **What** | Golden-set JSONL spec, LangSmith `evaluate()` wiring, ragas RAG metrics, deepeval LLM-as-judge, LangGraph trajectory eval, CI regression gate, 4 references |
| **When** | Setting up quality measurement for a new chain, diagnosing regression after a model swap, building an eval gate for a PR, or publishing a benchmark |

## Key Features

1. **Statistically honest thresholds** — Paired Wilcoxon signed-rank test on 100-example golden sets with bootstrap CI; a raw mean delta of -1.8% on n=50 is noise, on n=200 is real — this skill names the numbers and the test
2. **Framework comparison with selection matrix** — LangSmith (traces + orchestration), ragas (RAG-specific metrics), deepeval (pytest-style LLM-as-judge), custom (exact-match, trajectory) compared on cost, setup effort, dependency weight, and integration shape — pick the right tool, not all four
3. **Trajectory eval for LangGraph agents** — Compare expected vs actual tool-call sequence with partial credit (full match, subset match, reorder penalty), plus LLM-as-judge fallback for free-form outputs when the trajectory is non-deterministic

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
