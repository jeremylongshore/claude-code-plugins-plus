# Golden Set Curation

The golden set is the bedrock. A bad golden set — too small, biased to easy
cases, unversioned, drifting — makes every downstream metric a lie. This is
the process we use.

## Format: JSONL + version tag

One example per line. Minimum schema:

```json
{
  "id": "gs-0001",
  "input": "What's the refund policy for SKU ABC-42?",
  "expected": "Refunds within 30 days with original receipt; see policy link.",
  "contexts": ["policy_v3_refunds.md#section-4"],
  "tags": ["refund", "policy-lookup"],
  "difficulty": "easy",
  "added": "2026-03-14",
  "annotator": "jlongshore",
  "dataset_version": "2026.03"
}
```

Fields in detail:

| Field | Required? | Purpose |
|---|---|---|
| `id` | Yes | Stable identifier; never reused across splits |
| `input` | Yes | Exactly what the chain receives (do not pre-process) |
| `expected` | Yes | Gold answer — reference for correctness metric |
| `contexts` | For RAG | Ground-truth doc IDs for `context_recall` / `context_precision` |
| `tags` | Strongly recommended | Stratified reporting (e.g. refund queries vs product queries) |
| `difficulty` | Strongly recommended | Keep easy:medium:hard ~= 3:5:2 so the set is not skewed |
| `added`, `annotator` | Recommended | Audit trail |
| `dataset_version` | **Required** | Pin a tag; eval runs reference this tag so results are comparable over time |

Store in repo at `evals/golden_set/v{version}.jsonl`. Treat the file as
immutable within a version — bump the version when you add/remove examples.

## Sample size guidance

| Claim you want to make | Minimum n |
|---|---|
| "This chain regressed" (paired A/B, same examples) | **50-100** examples |
| "Metric X is 82% ± 3%" (absolute claim with CI) | **200+** examples |
| "Chain A beats chain B on tag `refund`" (subgroup claim) | **50+ per subgroup** |
| Published benchmark / paper result | **500+** examples, stratified |

The 100-example paired-comparison floor comes from the statistical power of the
Wilcoxon signed-rank test at α=0.05: detecting a 5% true mean shift with 80%
power needs ~80-100 paired examples for binary correctness and ~40-60 for
continuous metrics (faithfulness in [0,1]). See `ci-integration.md` for the
Wilcoxon usage.

## Sourcing strategy

**Never write golden examples from imagination alone.** Imagined queries are
biased toward the cases you think are important, not the cases your users
actually send. Sample from real traffic.

1. **Export 7 days of production inputs** from your tracing system (LangSmith
   has `Client.list_runs` with filters). Redact PII.
2. **Stratify by tag or intent** — for a support bot, sample evenly across
   refund / shipping / product / account categories. Uniform sampling
   under-represents rare-but-important tags.
3. **Stratify by difficulty** — reserve ~30% hard cases (multi-hop, ambiguous,
   adversarial). A golden set that is all easy cases cannot detect regression
   on hard cases.
4. **Annotate manually** — two annotators per example, disagreements reconciled
   by a third. Reconciliation rate under 90% means your task definition is
   ambiguous; fix the definition before shipping the set.
5. **Adversarial examples (5-10% of set)** — prompt injections, off-topic
   queries, empty inputs, requests in the wrong language. Agents and chains
   that pass all happy-path but fail adversarial are a real category.

## Versioning and refresh cadence

- **Version tag format:** `YYYY.MM` for calendar-based releases, or `v1.0`,
  `v1.1` for milestone releases. Pin at eval time.
- **Refresh monthly** — add 10-20 new examples from recent traffic, retire
  examples that have become irrelevant (feature removed, policy changed).
- **Never edit past versions** — if an example was wrong, mark it deprecated
  in the new version but keep the old version immutable. Comparing v2026.03
  vs v2026.04 must always reproduce.
- **Keep a changelog** at `evals/golden_set/CHANGELOG.md`: which examples were
  added, removed, or re-annotated, and why.

## Annotation tool options

| Tool | Setup | Best for |
|---|---|---|
| **JSONL + git PRs** | Zero tooling; reviewer reads PR diff | Small sets (< 200 examples), single annotator |
| **LangSmith UI** | `langsmith` dataset with web annotation | Team of 2-5, reconciliation workflow built in |
| **Argilla** (open source) | Self-hosted or HF Spaces | Larger sets (1000+), multi-annotator with agreement metrics |
| **Label Studio** | Self-hosted | Complex labels (spans, hierarchies), already used for other NLP |

For a 100-example golden set with two annotators, JSONL + git PRs is enough.
Moving to LangSmith once you need reconciliation tooling pays off.

## Common pitfalls

- **Leakage from train to eval.** If your prompt engineer looked at eval
  examples while tuning prompts, the set is contaminated. Lock the eval set
  before prompt tuning, or maintain a held-out "blind" subset.
- **Over-specific expected answers.** If `expected` is one exact phrasing but
  ten paraphrases are equally correct, exact-match will under-report quality.
  Use an LLM-as-judge or semantic-similarity metric for open-ended outputs.
- **Stale ground truth.** Policy changed; expected answer is now wrong. Quarterly
  audit: re-review 10% of the set, flag drift.
- **Unbalanced difficulty.** If the set is 90% easy, a chain can regress hard
  cases from 40% to 10% and the aggregate score barely moves. Stratify and
  report per-difficulty.

## Minimum viable starting point

Shipping today? Build this:

1. 20 real queries from production, redacted.
2. Expected answers written by a domain expert, two-annotator reconciled.
3. Tags covering your top 4-5 intent categories, roughly even.
4. Saved as `evals/golden_set/v2026.04.jsonl` with a `dataset_version` field.
5. Reference version tag in your first eval run.

This is not enough for publishing, but it is enough to catch regressions in CI.
Grow to 100 over the next month.
