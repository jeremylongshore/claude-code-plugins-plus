# CI Integration: Gating PRs on Eval Regression

The goal: a pull request that changes a prompt, model, retrieval config, or
chain topology runs the eval suite and blocks merge if quality regressed.
Without it, "gut-feel" regressions land in main.

## Gating rules (the thresholds we use)

| Signal | Block merge if... | Why |
|---|---|---|
| Aggregate mean drop | **mean metric drops > 2.0%** (vs baseline on main) | Bigger than typical judge noise (~1%), small enough to catch drift |
| Per-example drop | **any single example drops > 5.0%** on metric | Catches "fixed A, broke B" trades that aggregate hides |
| Statistical significance | Wilcoxon signed-rank **p < 0.05** for paired eval | Ensures the drop is not noise at the current sample size |
| Cost | Judge cost > $15 per run | Prevents runaway judge calls |
| Runtime | Eval run > 20 minutes | Catches infinite-loop bugs in chains |

These are starting values — tune on your project. A prompt-engineering-heavy
repo might relax the per-example threshold; a safety-critical repo tightens it.

## Statistical significance: Wilcoxon signed-rank

Paired comparison on the same golden set before and after a change. Wilcoxon
is the right test — t-test assumes normal distribution, which LLM metrics
rarely satisfy (bimodal on easy/hard splits, bounded at 0 or 1).

```python
from scipy.stats import wilcoxon

def paired_regression_check(
    baseline_scores: list[float],
    candidate_scores: list[float],
    alpha: float = 0.05,
) -> dict:
    """Check if candidate regressed vs baseline with statistical significance."""
    if len(baseline_scores) != len(candidate_scores):
        raise ValueError("Scores must be paired (same examples, same order)")
    n = len(baseline_scores)
    if n < 50:
        return {"verdict": "too_small", "n": n, "min_n": 50}

    diffs = [c - b for b, c in zip(baseline_scores, candidate_scores)]
    mean_delta = sum(diffs) / n

    # Wilcoxon tests whether the median paired difference is zero.
    # alternative="less" = testing for regression (candidate < baseline).
    stat, p_value = wilcoxon(diffs, alternative="less")
    significant_regression = p_value < alpha and mean_delta < 0

    return {
        "n": n,
        "mean_delta": mean_delta,
        "p_value": float(p_value),
        "significant_regression": bool(significant_regression),
        "verdict": "regression" if significant_regression else "no_regression",
    }
```

At n=100 and α=0.05, this detects a true regression of ~3-5% with ~80% power
on continuous metrics — which is why 100 is the working minimum for PR gates.

## Bootstrap CI for absolute claims

Wilcoxon tests "is there a regression" but does not produce a CI around the
mean. For "faithfulness is 0.82 ± 0.03" claims, use bootstrap:

```python
import random

def bootstrap_ci(scores: list[float], n_iter: int = 1000, ci: float = 0.95) -> tuple[float, float]:
    """Return (lower, upper) percentile bootstrap CI."""
    means = []
    n = len(scores)
    for _ in range(n_iter):
        resample = [random.choice(scores) for _ in range(n)]
        means.append(sum(resample) / n)
    means.sort()
    lo_idx = int(n_iter * (1 - ci) / 2)
    hi_idx = int(n_iter * (1 + ci) / 2)
    return means[lo_idx], means[hi_idx]
```

Report CI alongside every headline metric. A point estimate without CI is not
a claim — it's a guess.

## Judge-run quorum (LLM-as-judge variance)

LLM-as-judge scores vary ±5-15% across runs on the same example. Single-run
judges are not CI-ready. Run each judge call N=3 times and take the median:

```python
def judge_with_quorum(judge, prompt: str, n: int = 3) -> tuple[float, float]:
    """Run judge n times, return (median_score, stdev)."""
    import statistics
    scores = [float(judge.invoke(prompt).content.strip()) for _ in range(n)]
    return statistics.median(scores), statistics.stdev(scores)
```

If stdev > 1.0 (on a 5-point scale) or > 0.2 (on a [0,1] scale), flag the
example for manual review — the judge is disagreeing with itself, so its
score is not trustworthy regardless of median.

## GitHub Actions workflow

`.github/workflows/eval.yml`:

```yaml
name: LLM Eval Gate

on:
  pull_request:
    paths:
      - 'prompts/**'
      - 'src/chains/**'
      - 'src/agents/**'
      - 'config/models.yaml'
      - 'evals/**'

jobs:
  eval:
    runs-on: ubuntu-latest
    timeout-minutes: 25
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'

      - run: pip install -e . && pip install -r evals/requirements.txt

      # Run eval on PR branch
      - name: Run eval on candidate
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
        run: python evals/run.py --output candidate.json

      # Run eval on main baseline
      - name: Run eval on baseline
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
        run: |
          git stash
          git checkout origin/main -- src/ prompts/ config/
          python evals/run.py --output baseline.json
          git checkout HEAD -- src/ prompts/ config/
          git stash pop || true

      - name: Compare and gate
        run: python evals/compare.py baseline.json candidate.json --gate

      - name: Post PR comment with deltas
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const comment = fs.readFileSync('eval_comment.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment,
            });
```

## `evals/compare.py` skeleton

```python
"""Compare baseline vs candidate eval runs. Exit non-zero on regression."""
import argparse, json, sys
from pathlib import Path

MEAN_DROP_THRESHOLD = 0.02   # 2% aggregate drop
PER_EX_DROP_THRESHOLD = 0.05 # 5% any-example drop

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--gate", action="store_true")
    args = parser.parse_args()

    base = json.loads(args.baseline.read_text())
    cand = json.loads(args.candidate.read_text())

    failures = []
    report_lines = ["# Eval Report", "", f"Dataset version: `{base['dataset_version']}`", ""]
    report_lines.append("| Metric | Baseline | Candidate | Delta |")
    report_lines.append("|---|---|---|---|")

    for metric in base["metrics"]:
        b = base["metrics"][metric]["mean"]
        c = cand["metrics"][metric]["mean"]
        delta = c - b
        flag = " REGRESSION" if delta < -MEAN_DROP_THRESHOLD else ""
        report_lines.append(f"| {metric} | {b:.3f} | {c:.3f} | {delta:+.3f}{flag} |")
        if delta < -MEAN_DROP_THRESHOLD:
            failures.append(f"{metric} dropped {abs(delta):.2%} (threshold {MEAN_DROP_THRESHOLD:.0%})")

    # Per-example regression check
    for ex_id, ex_base in base["per_example"].items():
        ex_cand = cand["per_example"].get(ex_id, {})
        for metric, b_score in ex_base.items():
            c_score = ex_cand.get(metric, 0)
            if c_score < b_score - PER_EX_DROP_THRESHOLD:
                failures.append(
                    f"Example {ex_id} / {metric}: {b_score:.2f} → {c_score:.2f}"
                )

    Path("eval_comment.md").write_text("\n".join(report_lines))

    if args.gate and failures:
        print("Regression detected:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## Secret and cost safety

- **API keys:** GitHub Secrets only. Never expose in logs.
- **Spend caps:** Set per-key monthly limits on OpenAI/Anthropic dashboards.
  Evaluators with bugs can burn through budget in minutes.
- **Rate limits:** Use `langchain-core`'s built-in retry + `asyncio.Semaphore`
  to cap concurrency. A 100-example eval with 4 ragas metrics = 400 LLM calls;
  parallelized at 10 concurrent is manageable, at 50 triggers 429s on most
  tiers.
- **Caching:** LangSmith caches evaluator results by `(dataset_version, chain_version)`
  keys. Re-running an unchanged PR should be nearly free.

## When to run vs skip

Run on every PR that touches:

- `prompts/**`, `src/chains/**`, `src/agents/**`
- Model config (`config/models.yaml`)
- Retrieval config, embedding model, chunking
- The eval set itself (to verify the set still runs)

Skip for documentation-only changes, CI config, or test fixtures. Path
filters in the `on.pull_request.paths` section handle this.

## Slack / PR-comment surface

Post the delta table as a PR comment with ✓/✗ per metric. Engineers triage
regressions in the PR conversation, not in a separate dashboard.

For nightly main-branch runs, post a daily summary to Slack with the metric
trend (`#ml-eval` channel). Drift over weeks is the hardest-to-catch failure
mode — a daily digest catches it while daily PRs cannot.
