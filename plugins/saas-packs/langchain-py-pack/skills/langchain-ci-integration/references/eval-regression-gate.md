# Eval Regression Gate

Wire the `langchain-eval-harness` eval suite into PR CI as a merge-blocking gate. Posts a metric-delta comment on every PR; blocks merge when aggregate drops >2% or any per-example drops >5%. Minimum sample size n=100 for meaningful signal.

## What this skill does NOT own

This skill owns the **CI plumbing** — the GHA job, the PR comment, the threshold policy, the required-status-check wiring.

The **harness itself** (LangSmith or local evaluators, metric definitions, example datasets, judge prompts) lives in `langchain-eval-harness`. Do not duplicate that content here.

## Threshold policy

| Signal | Threshold | What it catches | Action |
|--------|-----------|-----------------|--------|
| Aggregate score delta | < -2% | Systemic regressions across many examples | Block merge |
| Any single-example delta | < -5% | Quiet regressions averaged away in the aggregate | Block merge |
| Sample size | n ≥ 100 | Anything less is noise-dominated | Block job from running at n<100 |
| Wall time | < 10 min | Budget ceiling; go async if near limit | Switch to `asyncio.gather` concurrency |

**Why n ≥ 100.** With binary metrics (pass/fail) at p=0.8, the standard error of the mean at n=100 is ~4%. A 2% aggregate drop is at the edge of statistical signal but still discoverable with a one-sided test. Below n=30, the SE balloons past 7% and every PR looks like a regression.

**Why -2% aggregate AND -5% per-example (both, not either).** The aggregate catches broad regressions. The per-example catches narrow ones — e.g., a prompt tweak that fixes 90 cases but breaks 5 specific edge cases. Each gate misses what the other catches.

## The CI wrapper (`scripts/run_eval.py`)

```python
"""Run the eval harness at two refs, compare, post PR comment, exit nonzero on regression."""
import argparse, json, os, subprocess, sys, pathlib, tempfile

AGG_DROP_LIMIT = 0.02
PER_EX_DROP_LIMIT = 0.05


def run_eval_at(ref: str, n: int) -> dict:
    """Check out `ref` in a worktree, run the harness, return results dict."""
    with tempfile.TemporaryDirectory() as td:
        subprocess.check_call(["git", "worktree", "add", td, ref])
        try:
            out = subprocess.check_output(
                ["python", "-m", "eval_harness", "--n", str(n), "--json"],
                cwd=td,
            )
            return json.loads(out)
        finally:
            subprocess.check_call(["git", "worktree", "remove", td])


def format_comment(base: dict, head: dict, agg_delta: float, per_ex_drops: list) -> str:
    verdict = "PASS" if agg_delta >= -AGG_DROP_LIMIT and not per_ex_drops else "FAIL"
    lines = [
        f"## Eval regression gate: **{verdict}**",
        "",
        f"- Sample size: n={len(base['examples'])}",
        f"- Baseline ref: `{base['ref']}`  |  Head ref: `{head['ref']}`",
        "",
        "| Metric | Baseline | Head | Δ |",
        "|---|---|---|---|",
    ]
    for metric in base["aggregate_by_metric"]:
        b = base["aggregate_by_metric"][metric]
        h = head["aggregate_by_metric"][metric]
        arrow = "↓" if h < b else ("↑" if h > b else "=")
        lines.append(f"| {metric} | {b:.3f} | {h:.3f} | {arrow} {h-b:+.3f} |")
    if per_ex_drops:
        lines += ["", "### Per-example regressions (>5% drop):", ""]
        for ex_id, drop in per_ex_drops:
            lines.append(f"- `{ex_id}`: dropped {drop:.1%}")
    return "\n".join(lines)


def post_pr_comment(body: str) -> None:
    pr = os.environ.get("PR_NUMBER")
    if not pr:
        print(body)  # fallback for local runs
        return
    subprocess.check_call([
        "gh", "pr", "comment", pr, "--body", body,
    ])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--baseline", required=True)
    p.add_argument("--head", required=True)
    p.add_argument("--n", type=int, default=100)
    args = p.parse_args()

    if args.n < 100:
        print(f"::error::n={args.n} is below statistical floor (100)", file=sys.stderr)
        sys.exit(2)

    base = run_eval_at(args.baseline, args.n)
    head = run_eval_at(args.head, args.n)

    agg_delta = head["aggregate"] - base["aggregate"]
    per_ex_drops = []
    for ex in base["examples"]:
        eid = ex["id"]
        if eid not in head["scores"]:
            continue
        drop = base["scores"][eid] - head["scores"][eid]
        if drop > PER_EX_DROP_LIMIT:
            per_ex_drops.append((eid, drop))

    comment = format_comment(base, head, agg_delta, per_ex_drops)
    post_pr_comment(comment)

    if agg_delta < -AGG_DROP_LIMIT or per_ex_drops:
        print("::error::eval regression gate failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## PR comment template (rendered example)

```markdown
## Eval regression gate: **FAIL**

- Sample size: n=100
- Baseline ref: `origin/main`  |  Head ref: `HEAD`

| Metric | Baseline | Head | Δ |
|---|---|---|---|
| exact_match | 0.810 | 0.760 | ↓ -0.050 |
| bleu | 0.620 | 0.610 | ↓ -0.010 |
| judge_score | 4.200 | 4.150 | ↓ -0.050 |

### Per-example regressions (>5% drop):

- `multi-turn-007`: dropped 15.0%
- `edge-case-042`: dropped 8.0%
```

## Required-status-check wiring

GitHub Settings → Branches → Branch protection rule for `main`:

- Check **Require status checks to pass before merging**
- Add `eval regression (n=100)` to the required list
- Also add `unit (py3.10)`, `unit (py3.11)`, `unit (py3.12)`, `lint + dryrun`

With this config, `gh pr merge` refuses to merge until the eval job exits 0. Admin overrides are possible but logged.

## When to tune thresholds

Default -2% / -5% is tuned for **deterministic-ish** evals (exact match, BLEU against a reference, or a well-calibrated judge). Loosen if your eval is naturally noisy:

| Eval type | Suggested aggregate limit | Suggested per-example limit |
|-----------|---------------------------|------------------------------|
| Exact-match / regex | -2% | -5% |
| BLEU / ROUGE | -3% | -7% |
| LLM-as-judge with a strong base model | -3% | -10% |
| LLM-as-judge with a cheap base model | skip the per-example gate; aggregate -5% only |

Do not loosen thresholds to quiet a flaky gate — that masks regressions. Fix the underlying noise (bigger n, better judge prompt, deterministic seeds where the provider supports them).

## Failure modes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Eval job always fails on first PR against a new branch | No baseline run on `origin/main` | Ensure `fetch-depth: 0` in checkout; cache `main` results |
| Flaky pass/fail at the threshold boundary | n too small | Bump to n=200 for PRs; costs roughly 2× but SE shrinks √2 |
| Job times out at 10 min wall clock | Serial eval loop | Switch harness to `asyncio.gather` with provider rate-limit semaphore |
| PR comment not posted | `permissions: pull-requests: write` missing or `GH_TOKEN` env not set | Add `permissions` block to workflow; set `GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` on the step |
| Per-example drops flagged but they are new examples added in the PR | Base ref does not have those example IDs | Filter `per_ex_drops` to only example IDs present in `base["scores"]` (the wrapper above does this) |

## Cross-references

- Eval harness definition, metric selection, judge prompts — `langchain-eval-harness`
- Warning-filter policy that keeps `-W error` green during eval — [GHA Workflow Reference](github-actions-workflow.md)
- Local eval debugging workflow — `langchain-local-dev-loop` (F23)
