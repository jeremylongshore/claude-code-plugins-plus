---
title: "Coverage Said 69%, Mutation Testing Said 25%"
description: "A repo at 69% line coverage scored 24.88% on mutation testing—and the rules engine that touches user email scored 0.00%. Coverage said fine; Stryker didn't."
date: "2026-06-28"
tags: ["testing", "typescript", "ci-cd", "devops", "automation"]
featured: false
---
Sunday 2026-06-28. intent-mail repo, fresh Stryker baseline run. The coverage gate reported green: 69.09% line coverage. Three seconds later, mutation testing reported 24.88%. The rules engine—the code that actually mutates user email—reported 0.00%.

That zero is the story.

## The Gap

Coverage counts lines. Mutation testing counts assertions. When a 535-line end-to-end suite exercises a piece of code but doesn't assert on its internal logic, coverage sees a line executed and calls it a win. Mutation testing inverts a single boolean operator in that line, runs the suite again, and if the outcome is the same, marks that mutant as *survived*. The engine had 301 mutants and zero of them were killed—not because there were no tests, but because the tests that ran the code never asserted on the code's *decision logic*.

Here's the real shape of it:

| File | Line Coverage | Mutation Score | Killed | Survived | No-coverage Mutants |
|---|---|---|---|---|---|
| `connectors/shared/retry.ts` | — | 76.27% | 44 | 9 | 5 |
| `storage/token-crypto.ts` | — | 52.53% | 52 | 17 | 30 |
| `ai/daily-digest.ts` | — | 34.66% | 61 | 85 | 30 |
| **`rules/engine.ts`** | — | **0.00%** | 0 | 0 | **301** |
| **Overall repo** | **69.09%** | **24.88%** | 157 | 111 | 366 |

The engine had no co-located unit tests. It was exercised end-to-end—so it counted toward line coverage—but its specific logic was never pinned. Flip a condition in the engine, and the outcome (was the email moved?) often stays the same. The assertion lives at the wrong level.

## Code Coverage vs. Mutation Testing: What's the Difference?

Code coverage counts whether a line executed. Mutation testing counts whether that line's behavior is actually asserted. Run both on one repo and you can get 69% line coverage beside a 24.88% mutation score—because a line can execute in dozens of tests while none of them pin down what it should do.

A *mutant* is a one-character change: `===` becomes `!==`, `&&` becomes `||`, a `>` becomes `>=`. Stryker performs *fault injection*—it injects the mutant, runs the test suite, and counts:

- **Killed**: a test failed (the mutant was caught).
- **Survived**: all tests passed (the mutant hid).
- **No-coverage**: no test executed that line at all.

The 301 mutants in the engine were all no-coverage. Stryker never even got to run them against a test, because there was no unit test visiting that file.

Meanwhile, the repo's overall line coverage sat at 69.09%—and the engine's lines were executed via the E2E path, counting toward that number. Coverage says "this line ran." Mutation testing says "this line's behavior is pinned down by assertions"—call it assertion coverage. They are not the same metric, and a [green CI run](/posts/when-green-ci-proves-nothing/) only tells you about the first.

## The Stryker Setup

```json
{
  "packageManager": "npm",
  "testRunner": "vitest",
  "reporters": ["html", "clear-text", "progress"],
  "coverageAnalysis": "perTest",
  "mutate": [
    "src/rules/engine.ts",
    "src/connectors/shared/retry.ts",
    "src/storage/token-crypto.ts",
    "src/ai/daily-digest.ts"
  ],
  "thresholds": {
    "high": 80,
    "low": 60,
    "break": null
  }
}
```

The `mutate` array targets four high-value pure-logic files. Stryker baseline runs in ~30 seconds. The `break: null` is deliberate: report the score, but do not fail CI. Establish a baseline first. Ratchet later.

This is the inverse of the "fail immediately on every finding" instinct. A fresh gate that blocks on day one gets disabled by the next engineer. Report-only first. Let the team see the numbers. Then make it enforceable—and [honor the gate](/posts/honor-the-gate-when-the-verdict-is-inconvenient/) when its verdict is inconvenient.

## Why E2E Wasn't Enough

The same day, a 535-line end-to-end suite was added:

```typescript
describe("rules engine E2E", () => {
  const tmpDir = mkdtempSync(join(tmpdir(), "intentmail-"));
  const dbPath = join(tmpDir, "test.db");
  const testMasterKey = "e".repeat(64); // 64-char hex = 32-byte AES-256 key
  
  beforeAll(() => {
    process.env.INTENTMAIL_DB_PATH = dbPath;
    process.env.INTENTMAIL_MASTER_KEY = testMasterKey;
  });

  it("applies a rule and writes an audit log", async () => {
    // Create account → upsert emails → create rule → run it → assert outcome
    const emails = await db.getEmailsByRule(ruleId);
    expect(emails).toHaveLength(1);
    expect(emails[0].labels).toContain("archived");
    
    const auditLog = await db.getAuditLog(ruleId);
    expect(auditLog).toHaveLength(1);
    expect(auditLog[0].action).toBe("move");
  });
});
```

This is *good* and necessary. It proves the wiring: condition → action → side effect. But it asserts on the outcome (was the email moved?), not the logic (did the condition comparison return true or false for this specific case?).

Here's the subtle part. The engine's 301 mutants didn't even *survive*—they came back as **no-coverage**. At baseline time, Stryker found no co-located unit test pinning `engine.ts`, so it never ran those mutants against an assertion at all. The E2E suite executes the engine, but it asserts through the storage layer on the final state—which is exactly why the documented next step is a co-located `engine.test.ts`, not more end-to-end tests.

The other three files show the milder failure mode—a mutant that *is* covered but still survives. When a test executes a mutated line yet only checks the outcome, the mutant lives. Take a condition in the engine:

```typescript
// Original
if (email.subject.includes(rule.condition.value)) {
  
// Stryker mutant: flip the condition
if (!email.subject.includes(rule.condition.value)) {
```

An E2E test that asserts only on the final database state can let this flip through. Unless a fixture exercises both the matching and the non-matching branch—full branch coverage—*and* checks each one, inverting the condition can still leave the rows where the test expects them. The test never asserted "for this subject, the condition must return true"—so the mutant lives. That's the failure mode that left 85 mutants alive in `daily-digest.ts`, where tests did run. The engine's case is worse: no unit test ran at all.

Line coverage: ✓ (the line executed via E2E).  
Mutation coverage: 0 (the logic was never asserted at the unit level).

## Why Not Just Block On It?

Because a gate that reports a baseline truth on day one and gets disabled by day three is worse than no gate at all. The 24.88% score is real and uncomfortable. Flip `break` from `null` to `60`, and the suite fails immediately. The next engineer to touch this codebase sees a broken CI, disables the gate, deletes the stryker script, and ships. The baseline evaporates.

Instead: report-only for one development cycle. Let the team see the number. Add co-located unit tests to `src/rules/engine.test.ts` until the engine clears `low: 60`. Then flip `break: 60` and make it a ratchet: the mutation floor can only move up.

This is the same discipline as the L5 security scan wired the same day—gitleaks + OSV, both report-only, both feeding into `tests/TESTING.md` as the single source of truth for "which gates are enforced now, which are baseline, which are deferred?"

## Also Shipped

The same day closed two beads: **GCP Deployment** (won't-do, 592 lines deleted—`deploy.yml`, `drift.yml`, `infra/`), and **Test Coverage** (paid down lint debt, promoted `no-case-declarations` to error, adopted dotenv 17 + commander 15, 9 GitHub Actions bumps, closed children). The security scan job is non-blocking (`continue-on-error: true`) because 5 `fix=NONE` advisories live in duckdb's native build chain—accepted and documented until upstreams ship.

## The Transferable Rule

Coverage measures attendance. Mutation testing measures whether anyone was paying attention. A green coverage gate tells you code was executed. A green mutation gate tells you code's behavior was asserted. They are not the same gate. If your mutation score is much lower than your line coverage, your tests are outcome-level and your logic is untouched. Add assertions closer to the decision points. Start with report-only. Then ratchet.

## Related Posts

- [Green CI Proves Nothing: Why Your Tests Gate Zero Calls](/posts/when-green-ci-proves-nothing/) — a passing test suite that asserts on nothing.
- [Honor the Gate When the Verdict Is Inconvenient](/posts/honor-the-gate-when-the-verdict-is-inconvenient/) — the discipline of trusting the gate's verdict.
- [When LLM Output Lies Instead of Crashing](/posts/when-llm-output-lies-instead-of-crashing/) — the same intent-mail codebase: "it ran without erroring" is not "it's correct."

<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "BlogPosting",
  "headline": "Coverage Said 69%, Mutation Testing Said 25%",
  "description": "A repo at 69% line coverage scored 24.88% on mutation testing—and the rules engine that touches user email scored 0.00%. Coverage said fine; Stryker didn't.",
  "datePublished": "2026-06-28T08:00:00-05:00",
  "dateModified": "2026-06-28T08:00:00-05:00",
  "keywords": "mutation testing, code coverage, mutation score, Stryker, test quality, CI/CD, unit testing",
  "wordCount": 1200,
  "author": {
    "@type": "Person",
    "name": "Jeremy Longshore"
  }
}
</script>
