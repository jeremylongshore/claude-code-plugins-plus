---
title: "A v1.0 Is a Gate, Not a Tag"
description: "Why release gates should accept GO with conditions, not binary GO/NO-GO. How ICO v1.0.0 shipped with documented gaps and a same-day v1.0.1."
date: "2026-05-18"
tags: ["release-engineering", "ci-cd", "typescript", "testing", "monorepo"]
featured: false
---
Two beads were open at the start of 2026-05-18. E10-B11 was the v1.0 release-readiness gate. E10-B12 was the v1.0 release cut, blocked-by-design on B11. Epic 10 was the last epic in `intentional-cognition-os` (ICO). The release pipeline was wired through `/release`. Everything that mattered had to clear one ritual.

Five npm releases shipped that day: v0.21.0 → v0.22.0 → v0.22.1 → v0.22.2 → **v1.0.0** → v1.0.1. The interesting one is v1.0.0, because the gate said **GO with conditions**, not GO. And the same-day v1.0.1 is the proof that "GO with conditions" is the correct verdict shape for a real release, not a binary.

## The 3× degradation gate

The release ran on top of fresh benchmark infrastructure. `625691e` and `f7bd287` closed out E10-B06 (performance profiling) with a 500-source large-corpus benchmark. The headline addition was a **3× degradation gate** — a configurable cap (default 3.0) that fails the run if per-unit cost at large scale exceeds 3× the moderate-corpus baseline.

The gate is intentionally narrow:

```ts
// utils/degradation.ts — gate stays honest by NOT inferring per-unit costs
export function computeDegradation(
  moderatePerUnitMs: number,
  largePerUnitMs: number,
  cap = 3.0
): { ratio: number; pass: boolean } {
  if (moderatePerUnitMs === 0) {
    return { ratio: Infinity, pass: false }; // catch degenerate samples loudly
  }
  const ratio = largePerUnitMs / moderatePerUnitMs;
  return { ratio, pass: ratio <= cap };
}
```

The runner does per-unit derivation BEFORE calling the gate. Ingest's `perFile.medianMs` is already per-unit (each iteration was one file). Lint's `result.medianMs` is whole-workspace, so the runner divides by page count first. Putting that decision in the runner instead of the gate is the difference between "gate that knows what it's measuring" and "gate that guesses at the measurement units."

Results at 500 sources: ingest 1.25× (PASS), lint 0.33× (PASS — got faster at scale, likely amortized constants). The gate had teeth and the system passed cleanly.

## The release-readiness checklist (E10-B11, PR #73)

Eight items, verified item-by-item, recorded honestly. No "looks good to me" entries:

1. **CI passes** — all 4 jobs green on last 3 main runs
2. **Evals pass** — smoke eval clean; retrieval/citation/compilation handlers wired with 30+ unit tests
3. **Coverage targets** — PARTIAL. Types 100%, kernel 84.6% (target 90%), compiler 62.3% (target 80%), CLI 45.2% (target 70%)
4. **Docs updated** — current per E10-B07/B08
5. **CHANGELOG complete** — auto-generated, current through v0.22.0
6. **No critical beads open** — only B11 (this) + B12 (release cut, blocked by design)
7. **User journey walkthrough** — `ico init` → status → 14-command CLI surface, live smoke-tested
8. **Performance targets met** — ingest 200× headroom, lint 3000× headroom, 3× degradation gate PASS

Verdict: **GO with two conditions.**

- **C1:** `ico --version` reported `0.1.0` (a stale kernel constant) instead of the published `0.22.x`. Fix in-cut.
- **C2:** Coverage shortfall on kernel/compiler/cli. Documented as post-v1, not blocking. 1,210 passing tests, zero known bugs.

That verdict is the artifact. Most release rituals make GO/NO-GO a binary. The conditional verdict is honest: state the gap, decide if it blocks, ship if it doesn't, document the gap permanently if it doesn't.

## What "GO with conditions" actually means

A conditional release verdict is the three-state model: **fix what's fixable in-cut, document what isn't, ship anyway.** Unlike a binary GO/NO-GO gate that forces a boolean choice, a conditional gate acknowledges that real releases ship with known imperfections. The conditions are documented forever in the release record — no lying about readiness, no pretending gaps don't exist, but no unnecessary delays waiting for the perfect threshold that never comes.

## Why not GO/NO-GO binary?

Binary GO/NO-GO encourages two bad behaviors.

**Behavior one: lower the bar to ship.** "The version-string bug is fine, users will figure it out." The release ships, the operator-visible defect ships with it, and the next person debugging an environment ends up reading the wrong build into their incident postmortem.

**Behavior two: delay until the gate is perfect.** Coverage targets met on a Tuesday that never comes. Kernel at 84.6% is allegedly not 90%, so v1.0 slips. Then 90% becomes 95%, because some new code landed during the wait. The gate becomes a treadmill.

Coverage at kernel 84.6% / compiler 62.3% / CLI 45.2% with 1,210 passing tests and zero known bugs **is shippable**. Blocking v1.0 on coverage uplift would have been a bigger lie than shipping with documented shortfalls. The AAR opens C2 as a post-v1 bead for the next planning cycle. The truth is in the record.

C1 is the inverse case — `ico --version` reporting the wrong number is shippable but ugly, and the fix is small. So fix it in-cut, document it, move on. The gate didn't pretend C1 was fine; it just didn't pretend it was a v2.0-blocker either.

The prescription is a three-part rule, not a two-part one: **fix what's fixable in-cut, document what isn't, ship anyway.** Binary GO/NO-GO collapses three states into two and loses the most useful one — the "shippable with known imperfections" state where most real releases actually live.

## C1 fix: read your own version (PR #74)

`packages/cli/src/index.ts` had been importing `version` from `@ico/kernel`, which exported a hardcoded string. The kernel constant was never maintained in lock-step with the published CLI package — and **shouldn't be**, since they are independent artifacts on independent release cadences.

```ts
// packages/cli/src/index.ts — read from CLI's own package.json
function readCliVersion(): string {
  try {
    const pkgPath = new URL('../package.json', import.meta.url);
    const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));
    return pkg.version;
  } catch (err) {
    console.error('[ico] failed to read CLI package.json:', err);
    return '0.0.0-unknown'; // sentinel — CLI keeps working, operator sees clear msg
  }
}
export const cliVersion = readCliVersion();
```

The try/catch is load-bearing. `readCliVersion()` runs at module load, BEFORE the process-level error handlers are installed further down the file. An uncaught throw here would surface as a raw Node stack trace and bypass the friendly `[ico]`-prefixed message convention every other CLI error uses. The sentinel path is what makes this safe to call at import time — the CLI keeps working, the operator gets a legible message, and the bug is visible without crashing.

The test was tightened in the same PR. `/^\d+\.\d+\.\d+/` (no end anchor — would accept nonsense like `0.22.1.99`) became:

```ts
expect(cliVersion).toMatch(/^\d+\.\d+\.\d+(-[\w.-]+)?$/);
```

Strict semver core plus optional pre-release tag. The previous regex was a one-character bug; the fix is one character plus an opt-in pre-release group.

## The cut itself (52fa7a4 → v1.0.0)

The cut commit was tiny: 11 files, +54/-10 lines. It did one thing: aligned **all 6 workspace `package.json`** + `version.txt` + `kernel/src/version.ts` at 1.0.0.

The auto-release workflow had been bumping the root `package.json` and `version.txt` only — internal packages had drifted to 0.1.0 or 0.22.1 depending on history. `/release` Phase 3 caught the drift. Phase 5 required explicit SHA approval before any push (`f1a627b`). Phases 6-8 ran atomically.

Verified at v1.0:

- 1,210 / 1,210 tests pass across 5 packages
- Lint + typecheck clean
- escape-scan REFUSE=0 CHALLENGE=0 FLAG=0
- `ico --version` reports `1.0.0`

## The tarball turned out incomplete (v1.0.1, same day)

During the actual `npm publish` flow, the pack dry-run reported **7 files** when expected was 9: dist + package.json, no README, no LICENSE. The CLI's `package.json` declared:

```json
"files": ["dist", "README.md", "LICENSE"]
```

But the CLI directory didn't OWN those files. The canonical `README.md` and `LICENSE` live at the monorepo root.

Fix landed inline before the real publish:

```ts
// packages/cli/tsup.config.ts — copy README + LICENSE at build time
export default defineConfig({
  // ... entry, format, dts, sourcemap ...
  onSuccess: 'cp ../../README.md ../../LICENSE ./',
});
```

The copies are gitignored (their source of truth is the repo root). v1.0.0 on npm now includes both. No version bump for the build-infra fix itself, but the same day shipped v1.0.1 for the next user-visible change.

This is the test of whether "GO with conditions" was the right shape. A binary GO/NO-GO ritual would have caught the version string (C1) and either fixed it before re-running the whole gate or punted to v1.0.1. The conditional model said: ship, here's what we know is imperfect. When the tarball turned out incomplete during the actual publish — a discovery that **couldn't** have been made during gate verification, because it only surfaces in the publish pipeline itself — the answer was just: ship v1.0.1 the same day. No drama. No "release is broken" panic. The model already accepted that real releases generate follow-on releases.

## AAR same day

`d17e10e docs(aar): v1.0.0 release after-action report` landed within hours. Three lessons-for-next-release, captured while they were still warm:

1. **Beads JSONL/Dolt sync flapping** during multi-PR sessions — repeated need to re-close beads after merges. Filed as a follow-up to investigate the sync ordering.
2. **Auto-release workflow bumps root + `version.txt` only** — should bump `packages/*/package.json` in lock-step. The 11-file cut commit was entirely correcting drift the workflow could have prevented.
3. **`/release` skill execution worked as designed** — Phase 0 surfaced no blockers, Phases 1-3 caught the version drift, Phase 5 required SHA approval, Phases 6-8 atomic.

Same-day AAR is non-negotiable. The version-drift issue, the tarball issue, the conditional-verdict pattern — all of them lose 80% of their teaching value if you write the AAR a week later, after the warm memory of "wait, why didn't the workflow catch that?" has faded into "yeah, we shipped, it was fine."

## Also shipped

The release gate constrained the v1.0.0 cut, not the working day. Three other repos kept moving in parallel — exactly the behavior the conditional-verdict model is designed to enable. A release that takes the whole org offline isn't a release ritual; it's an outage.

- **hustle:** Phase 3 auth landed in three commits — NextAuth + Drizzle/SQLite infrastructure, dashboard cutover, password reset flow. Coordinated migration from the previous auth stack on a single feature branch.
- **claude-code-slack-channel:** ACP session/cancel boundary adapter extracted into a module, and JSON-RPC `id` widened to nullable per spec §5.1 (#172, #173).
- **claude-code-plugins:** Six PRs — repo quality audit, private vulnerability reporting enabled, validator discovers root-level `SKILL.md` (Anthropic-spec layout), slack-channel mirror stopped stripping upstream tests, blog cross-post infra fix.

## Related Posts

- [Honest perf benchmarks for a paid-API compiler](/blog/honest-perf-benchmarks-paid-api-compiler/) — yesterday's post on the benchmark infrastructure that fed this release gate
- [Five releases in fifteen minutes: Mandy cutover and freeze break](/blog/five-releases-fifteen-minutes-mandy-cutover-and-freeze-break/) — earlier five-releases-in-a-day pattern
- [GitHub release workflow: uncommitted changes and semantic versioning](/blog/github-release-workflow-uncommitted-changes-semantic-versioning/) — related release-engineering theme
