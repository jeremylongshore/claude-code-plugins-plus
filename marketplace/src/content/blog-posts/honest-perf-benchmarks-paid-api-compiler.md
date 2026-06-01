---
title: "Honest Perf Benchmarks for a Paid-API Compiler"
description: "Four PRs, three releases, and a benchmark suite that won't lie to you: seeded-RNG corpora, double-gated Claude scenarios, and skipped-but-recorded records."
date: "2026-05-17"
tags: ["typescript", "testing", "architecture", "ci-cd", "ai-agents"]
featured: false
---
`intentional-cognition-os` is a TypeScript "compiler" — markdown sources go in one end, a structured artifact comes out the other, and several of the middle stages call paid Claude APIs to do the cognitive work. Up to today there were zero performance gates on any of it. No baseline, no regression alarm, no "did that refactor make ingest 4× slower" check.

The benchmark suite that landed across four PRs answers two design questions that had to be settled before a single line of timing code got written:

1. How do you compare numbers across machines when half the corpus is randomly generated text?
2. What do you do about the steps that cost real money on every run?

Get either answer wrong and the benchmark suite is worse than no benchmark suite — it produces numbers that look authoritative and aren't.

## The corpus has to be byte-identical

The first scenario — `ingest` — needs a corpus. Hand-curated fixtures committed to disk were considered and rejected: they don't scale, they go stale, and they encode whoever-wrote-them's idea of "representative." A generator is the right answer, but a generator has to be deterministic or before/after diffs are noise.

The generator uses a seeded `mulberry32` PRNG and pulls UUIDs from the same stream:

```typescript
function mulberry32(seed: number) {
  return function () {
    let t = (seed += 0x6d2b79f5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function seededUuidV4(rand: () => number): string {
  // 16 bytes from the seeded stream, version + variant nibbles set per RFC 4122
  const bytes = new Uint8Array(16);
  for (let i = 0; i < 16; i++) bytes[i] = Math.floor(rand() * 256);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  return formatUuid(bytes);
}
```

The non-obvious trap is `crypto.randomUUID`. It would have looked correct, passed every unit test, and silently produced different UUIDs on every run — so every "identical" corpus would have differed in the front-matter `id` field. That breaks ingest's content-hash cache in different ways on different machines. Same seed, same count, same body-word count yields byte-identical output everywhere. That's the contract.

One more gotcha worth a sentence: the corpus generator writes front matter through `gray-matter`, which quotes string values. The compiler's wiki-page validator uses a hand-rolled YAML parser that does NOT strip quotes — so wiki fixtures emit all values unquoted. A quoted `compiled_at` would arrive at Zod's datetime check with literal `"` characters in it and fail. Two parsers, two rules, documented inline at the parser boundary.

## An API key is not consent

The render, compile, and ask scenarios call Claude. Running them on every CI pass would either drain a budget or quietly stop running when the budget hit zero. Neither is acceptable.

The gate is two env vars, both required:

```bash
ANTHROPIC_API_KEY=sk-ant-... \
ICO_BENCH_INCLUDE_CLAUDE=1 \
pnpm --filter @ico/benchmarks bench
```

From PR #70's design notes, kept verbatim because the framing matters:

> The double gate is intentional. An API key alone is not consent — many developers have it set for normal CLI use. `ICO_BENCH_INCLUDE_CLAUDE` is the explicit "yes, burn tokens on this benchmark run" signal.

This pattern shows up elsewhere — `CI=true` plus `RUN_E2E=1`, prod credentials plus `--really-really-yes`. The shape is the same: one signal proves capability, the second proves intent. A single-gate design fails open the first time someone forgets which shell they're in.

## Skipped is not zero

The interesting design call was what to do when the gate is closed. The wrong answers:

- Don't run, don't record. Trend tooling then can't tell "we stopped running render" from "render still passes."
- Record a zero. Trend tooling thinks render got infinitely fast and stops alarming.

The right answer: record the scenario as `skipped: true` with a stable `skipReason`. `ScenarioRecord` is `Partial<CommonTiming>` so the timing fields legitimately don't exist on skipped records:

```json
{
  "name": "render",
  "skipped": true,
  "skipReason": "ICO_BENCH_INCLUDE_CLAUDE not set",
  "git_sha": "9c14f02",
  "node": "v22.21.0",
  "platform": "linux-x64"
}
```

A baseline-comparison script can now answer three different questions instead of two: did this scenario regress, did it improve, or did it not run? Skipped runs stay visible in the JSON timeline. They don't pollute the histogram, but they prove the scenario still exists and the runner saw it.

## The four PRs, briefly

- **PR #68** scaffolded the `packages/benchmarks/` workspace, the corpus generator, a `bench()` timer with warmup + N-iteration median + RSS delta, and the runner that captures git SHA, Node version, and platform into `results/<iso>-<sha>.json`. The `results/` directory is gitignored except `.gitkeep` — baselines get tracked explicitly, not by accident.
- **PR #69** added the `lint` scenario and moved `runLint`, `scanWikiPages`, `extractWikilinks`, `detectOrphans`, `LintResult`, and `SchemaError` out of `packages/cli/src/commands/lint.ts` into a new `packages/compiler/src/lint.ts`. The function only composes compiler + kernel primitives and has no CLI dependency — it belonged in the compiler the whole time. The CLI's lint command shrunk to a thin wrapper around commander wiring and `renderLintReport`. Side fix: `extractWikilinks` had a module-level `/g` regex whose `lastIndex` carried state between calls — the same class of bug that landed in PR #67 the day before. Fixed by constructing the regex per call.
- **PR #70** added the `render` scenario and the double-gate.
- **PR #71** added `compile` and `ask`, each using the same gating pattern. Roughly 70 lines of additions across both files — the gate had already done the hard work.

## Why not the obvious alternatives

Vitest's built-in `bench` was considered. It does microbenchmarks well and integrates with the existing test runner. It does not produce the JSON timeline shape needed for cross-run comparison, and bolting that on means owning the storage layer anyway. Build it once, build it right.

Committing fixture corpora to disk was considered. They go stale, balloon the repo, and encode one author's idea of "moderate." The seeded generator is reproducible AND parameterizable — same determinism guarantee, no committed binary blobs.

Running Claude scenarios always was considered for about a minute, then rejected on cost grounds. Even with caching, a benchmark suite that costs $2 per run on a busy day stops getting run.

## What the numbers say

Three scenarios ran on the dev box this afternoon (Claude-gated ones skipped because the opt-in wasn't set):

| Scenario | Median | Target | Headroom |
|---|---|---|---|
| ingest (per-file, 50 sources × 500 words) | ~9 ms | < 2 s | 220× |
| lint (50 sources + 30 wiki pages) | ~12 ms | < 30 s | 2400× |
| render | SKIPPED (no opt-in) | — | recorded |

The headroom isn't the point — those targets are deliberately generous because the goal is regression detection, not perf bragging. The point is that there are now numbers to regress *against*.

## Also shipped today

**claude-code-plugins repo audit.** A 232-line audit landed at `266-RA-AUDT-repo-quality-audit-2026-05-17.md` cataloguing a broken `/about` route, missing 404 handling, 14 stale `MS-OLDV` files still claiming v1.0.0 while the repo is at v4.30.0, and notebook content teaching the old 6-required-fields skill spec when the current spec requires 8. The first commit incorrectly flagged the wiki as empty, because `gh api repos/.../wiki` returns 404 even when the wiki has content — that endpoint isn't a content probe, it's a metadata probe with bad error semantics. Followup commit cloned the wiki, found 23 pages, and refreshed all of them with current numbers. Lesson noted inline: don't use API existence probes as content probes. Clone and read.

**claude-code-slack-channel threat model.** Added T11 (EchoLeak — instructions exfiltrated via legitimate-looking message replies) and invariant #7: admin verbs are not chat content. An operational key-management doc for the audit-signing key landed alongside the threat model update.

## The transferable pattern

Five scenarios in source tree, three actively measured, two gated behind explicit consent. The numbers that get reported are honest because the inputs are reproducible and the skipped runs are visible. Forget the opt-in flag and three scenarios show up as `skipped` in the JSON — they don't disappear, and they don't pretend to be zero.

Any benchmark suite that mixes deterministic and paid steps needs all three pieces: a deterministic corpus that survives machine swaps, an opt-in gate strong enough to mean something, and a record shape that distinguishes "didn't run" from "ran fast." Miss one and the suite will quietly lie to you the first time someone forgets which mode they're in. The lie is worse than the gap it filled.

## Related posts

- [Five Silent Failures in One Day](/blog/five-silent-failures-one-day/) — the regex `lastIndex` bug that re-appeared in PR #69 was one of these.
- [Deterministic-First, LLM-Advisory CI](/blog/deterministic-first-llm-advisory-ci/) — same principle: the deterministic gate decides, the paid gate informs.
- [Transitive CVE Clearance: A Dual-Layer Pattern](/blog/transitive-cve-clearance-dual-layer-pattern/) — the double-gate is the same shape as that two-layer defense.
