# Framework Comparison: LangSmith vs ragas vs deepeval vs Custom

Four tools, overlapping but distinct. Stacking all four is common; picking one
is also common. This reference is the decision map.

## Side-by-side matrix

| Dimension | LangSmith | ragas | deepeval | Custom (exact-match, trajectory) |
|---|---|---|---|---|
| **Primary purpose** | Trace capture + eval orchestration + dataset versioning | RAG-specific metrics (faithfulness, context precision/recall) | pytest-style LLM-as-judge assertions | Deterministic checks (exact match, regex, JSON schema, trajectory) |
| **Input shape** | `{input, expected}` dict rows | `{question, answer, contexts, ground_truth}` | `LLMTestCase(input, actual_output, expected_output, retrieval_context)` | Any — you own the row format |
| **Metric output** | Any evaluator you write; built-ins: correctness, cot_qa, labeled_criteria | Faithfulness, answer relevance, context precision, context recall, harmfulness | G-Eval, answer relevancy, faithfulness, contextual precision, bias, toxicity | Exact-match %, trajectory partial-match score, latency/token counters |
| **Judge LLM** | Your choice — pass a `ChatOpenAI` / `ChatAnthropic` to the evaluator | Default `gpt-4o-mini`, overridable | Default `gpt-4o`, overridable; supports local via `OllamaModel` | None (deterministic) |
| **Cost per 100-example run** | $0.50-$5 for judge + tracing is free tier | $1-$8 (four metrics × judge calls) | $1-$6 (per metric × judge) | ~$0 |
| **Setup effort** | Medium — `LANGSMITH_API_KEY` + dataset upload | Low — `pip install ragas` + dataset dict | Low — `pip install deepeval` + pytest | Low — write your own |
| **Best for** | Orchestration, trace-to-eval traceability, sharing runs with teammates | RAG pipelines where faithfulness and context recall matter | Pytest integration, CI assertions, LLM-as-judge at scale | Structured outputs, tool-call sequences, speed-critical checks |
| **Worst at** | Offline-only runs (needs API for dataset versioning) | Non-RAG chains (overkill, wrong metrics) | Non-pytest environments (the framework is pytest-shaped) | Semantic correctness (cannot judge paraphrase) |
| **Dependency weight** | `langsmith>=0.2` (lightweight) | `ragas>=0.2` pulls `datasets`, `pandas` | `deepeval>=2.0` pulls `pytest`, `rich`, `tenacity` | None beyond stdlib |

## Selection decision tree

```
Is it a RAG pipeline?
├── Yes → Start with ragas for the four core metrics.
│         Add LangSmith for orchestration + dataset versioning.
│         Optionally add deepeval if you need per-metric PR gates in pytest.
└── No
    ├── Is it an agent (LangGraph, tool-calling)?
    │   └── Yes → Custom trajectory eval (deterministic) + deepeval G-Eval
    │              for free-form final-answer quality.
    │              LangSmith for trace capture.
    └── No — is it a chain with a structured output?
        └── Yes → Custom exact-match / Pydantic-validate eval.
                   Add deepeval for soft metrics (tone, completeness).
                   LangSmith optional.
```

## Why you often stack 2-3

The tools do not compete; they layer.

- **LangSmith** captures the trace of every eval run — you can drill into a
  failing example and see the exact prompt, tool calls, and token usage. This
  is the "observability substrate" even if another tool computes the scores.
- **ragas** owns the RAG-specific math (context precision is rank-aware, not a
  simple set-overlap). Rewriting it correctly is not worth the time.
- **deepeval** owns the pytest ergonomics. `assert_test(test_case, metrics)`
  makes regressions fail CI the way engineers already understand.
- **Custom** handles the deterministic 60% of eval work (exact match, JSON
  shape, trajectory) at near-zero cost — use it for anything that does not
  need a judge LLM.

## Cost-efficiency rule of thumb

LLM-as-judge evaluators dominate cost. A 100-example run × 4 ragas metrics at
`gpt-4o-mini` is ~$1-2; the same at `gpt-4o` is ~$8-15. For nightly eval on
large suites, default to the mini tier, and upgrade to the full tier only
when judge-LLM disagreement is hurting the signal (see `ci-integration.md` on
judge-run quorum).

## Anti-patterns

- **Running all four frameworks on every example.** Overkill — you will pay
  $10-30 per run for signal you are not using. Pick the minimum set.
- **Using ragas for non-RAG chains.** Context precision against an empty
  context list returns 0 — which looks like a regression.
- **Using deepeval's `GEval` as the sole metric.** G-Eval is high-variance
  across judge runs (±10-15%). Pair with a deterministic metric or average
  over N≥3 judge runs (see `ci-integration.md`).
- **Skipping LangSmith dataset versioning.** If your eval set can drift, you
  cannot compare runs across weeks. Pin a dataset version tag.

## Official docs

- LangSmith evaluate: https://docs.smith.langchain.com/evaluation/tutorials/evaluation
- ragas metrics: https://docs.ragas.io/en/latest/concepts/metrics/overview/
- deepeval: https://docs.confident-ai.com/docs/evaluation-introduction
- G-Eval paper (variance characterization): https://arxiv.org/abs/2303.16634
