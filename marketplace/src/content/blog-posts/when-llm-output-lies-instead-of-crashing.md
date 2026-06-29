---
title: "When LLM Output Lies Instead of Crashing"
description: "An LLM-output parsing bug silently understated a cost report via case-sensitivity. One-line normalizer fix plus 5 defensive hardening steps."
date: "2026-06-27"
tags: ["python", "claude-code", "ai-agents", "debugging", "databricks"]
featured: false
---
Yesterday's post established that the LLM should never do the math—the `databricks-cost-leak-hunter` skill computes confirmed dollars via a SQL join to the customer's billing tables, not estimates. Bulletproof arithmetic.

But bulletproof math doesn't save you when the report that *displays* those numbers is built from the LLM's strings.

## The Silent Lie

The day after shipping PR #906, the Gemini review flagged 7 findings in `rank-and-report.py`—the Python script that ranks and formats those confirmed dollars into a CFO-facing report. Most were defensive coding hygiene. One was catastrophic.

The report's headline number—"Confirmed waste, monthly"—computed via a case-sensitive string comparison:

```python
confirmed_monthly = sum(c["monthly"] for c in ranked if c.get("kind") == "confirmed")
```

When the model emitted `"Confirmed"` (capital C) instead of `"confirmed"`, the row vanished from the sum. No crash. No error. The report rendered cleanly and reported ~$0/month in leak findings—even though the customer's data contained real, substantial leaks.

A crash would have been honest. This was worse: a well-formatted lie.

The fix is a single normalizer applied before every field comparison:

```python
def norm_kind(val: object) -> str:
    """Lowercase + strip a confidence tier so case/whitespace never silently drops a row."""
    return str(val or "").strip().lower()

confirmed_monthly = sum(c["monthly"] for c in ranked if norm_kind(c.get("kind")) == "confirmed")
```

One line. Placed at the parsing boundary where the LLM's output enters your code. Makes the difference between a report and a lie.

## The Other Boundaries

Same PR also hardened five more LLM-string interfaces. Three defensive parsing improvements:

- **Currency parsing**: `float(c.get("waste_30d_usd"))` raises when the model emits `"$1,200.50"` or `"1,200"`. New `parse_usd()` strips currency symbols and commas before conversion, returns 0.0 on non-numeric input instead of crashing the whole report.
- **stdin blocking**: without piped input on an interactive terminal, `sys.stdin.read()` hung. Now `sys.stdin.isatty()` exits 1 with a usage message—fail fast, don't hang automated pipelines.
- **JSON decode**: wrapped `json.loads()` to emit a clean error message instead of dumping a traceback on empty or malformed input.

Two more findings surfaced the same root cause as the silent-sum bug—case/whitespace sensitivity in the LLM's strings:

- **Output normalization for display**: the Confidence column and the `#1-line` callout rendered without normalizing, so a model-emitted `"AT-RISK"` or `"Confirmed"` showed up inconsistently instead of the spec form `Confirmed`/`Estimated`/`At-risk` (and lowercase `(confirmed)` in the callout). Same parse-boundary hazard as the math, surfaced in the UI instead.
- **The finding that wasn't a bug**: Gemini flagged a 🔴 CRITICAL SQL-injection on `spend-baseline.sql.json`, but inspection showed it was already handled in the merged #906 code—the warehouse id is injected at call time via `jq --arg wh "$DATABRICKS_WAREHOUSE_ID" '. + {warehouse_id: $wh}'`, parameter-bound, never string-interpolated into SQL text. Not every review finding is a real bug; you verify-and-close rather than change code. This adds honest texture: 7 findings, but 6 real bugs.

All changes verified: `ruff check` and `ruff format --check` green (CI-exact), plus functional smoke testing on currency strings, case-insensitive sums, and tty fast-exit.

The unifying pattern: every boundary where LLM output becomes code input is a failure surface. The SQL core is unassailable. The Python shell around it assumed well-formed strings. That's where the actual bugs lived.

Also shipped: version-coupling hygiene across `@intentsolutions/core`. Adopted `@intentsolutions/jrig-cli@0.1.0` as a root devDependency—and the subtle part: it transitively pulls `@core@0.9.0` but that copy stays nested under jrig-cli's own pnpm subtree, so the *root* `@core` pin stays exactly `0.4.1` and the kernel soak lanes are unaffected. Two versions of one package coexist by design. Separately bumped the *declared* kernel `@core` 0.4.1 → 0.9.0 as a governance-only change (no code imports of @core exist; it's the "C" in a V≤C≤K version-ordering invariant), and because authoring/v1 schemas are byte-identical between versions, the validator verdict is provably unchanged. The other boundary discipline of the day.

## Related Posts

- [The LLM Should Never Do the Math](/posts/llm-never-does-the-math/) — The SQL-first architecture that backs this fix.
- [CodeQL Caught the Race I Dismissed](/posts/codeql-caught-the-race-i-dismissed/) — Another review tool catching a bug the author had waved off; same shape as Gemini catching the silent lie.
- [MCP Server Auth: The API Is the Real Boundary](/posts/the-api-is-the-real-boundary/) — The boundary-discipline theme, one layer down the stack.
