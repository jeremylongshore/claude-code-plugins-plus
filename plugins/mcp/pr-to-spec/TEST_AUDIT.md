# Test Audit Report — pr-to-spec v0.6.0

Audit date: 2026-03-17
Before: 173 tests (16 files)
After: 248 tests (17 files)
Net gain: +75 tests

---

## Coverage Map

| Source File | Test File | Coverage Before | Coverage After |
|---|---|---|---|
| `src/core/ai/enhancer.ts` | `ai-enhancer.test.ts` | Good | Unchanged |
| `src/core/diff/spec-diff.ts` | `spec-diff.test.ts` | Good | Unchanged |
| `src/core/drift/detector.ts` | `drift.test.ts` | Good | +10 tests hardened |
| `src/core/drift/signals.ts` | (via drift.test.ts) | Good | Unchanged |
| `src/core/github/client.ts` | (via parsing.test.ts) | Good | Unchanged |
| `src/core/intent/schema.ts` | `intent.test.ts` | Good | +8 tests added |
| `src/core/intent/storage.ts` | `intent.test.ts` | Good | +8 tests added |
| `src/core/parsing/monorepo-detector.ts` | `monorepo-detector.test.ts` | Good | Unchanged |
| `src/core/parsing/pr-parser.ts` | `parsing.test.ts`, `scan.test.ts` | Good | +10 tests added |
| `src/core/parsing/review-parser.ts` | `review-parser.test.ts` | Good | Unchanged |
| `src/core/parsing/semantic-diff.ts` | `semantic-diff.test.ts` | Good | Unchanged |
| `src/core/protocol/envelope.ts` | `agent-protocol.test.ts` | Partial | +9 tests hardened |
| `src/core/rendering/comment.ts` | `rendering.test.ts` | Good | Unchanged |
| `src/core/rendering/json.ts` | `rendering.test.ts`, `cli-features.test.ts` | Good | +4 tests hardened |
| `src/core/rendering/markdown.ts` | `rendering.test.ts` | Partial | +4 tests added |
| `src/core/rendering/yaml.ts` | `rendering.test.ts` | Good | Unchanged |
| `src/core/risk/classifier.ts` | `risk.test.ts` | Good | Unchanged |
| `src/core/schema/prompt-spec.ts` | `schema.test.ts` | Partial | +9 tests added |
| `src/core/sources/github.ts` | `local-diff-source.test.ts` | Good | Unchanged |
| `src/core/sources/local.ts` | `local-diff-source.test.ts`, **`build-local-diff-source.test.ts`** (NEW) | **P0 Gap Closed** | +18 tests |
| `src/core/sources/types.ts` | (type-only) | N/A | N/A |
| `src/cli/scan.ts` | `scan.test.ts` | Partial | +10 tests added |
| `src/cli/check.ts` | (no direct tests) | P1 gap | No direct CLI tests (integration not feasible without mocking execSync) |
| `src/cli/intent.ts` | (no direct tests) | P2 gap | CLI command tested indirectly via intent schema/storage |

---

## Gaps Found

### P0 (Critical — Zero Coverage)

**`buildLocalDiffSource` modes**: The function `buildLocalDiffSource` in `src/core/sources/local.ts` had **zero test coverage**. The test file named `local-diff-source.test.ts` only tested `githubPRtoDiffSource`, `parseDiffStat`, and `parseNameStatus`. The three modes (`staged`, `commits`, `branch`) were completely untested.

**Remediation**: Created `tests/build-local-diff-source.test.ts` with 18 tests covering all three modes, including correct `source_type`, `base_ref`, `title`, `commits`, `head_ref`, and `author` field values.

### P1 (High — Partial Coverage)

**Schema optional fields**: `PromptSpecSchema` has 6 optional fields (`ai_enhanced`, `semantic_changes`, `declared_intent`, `drift_signals`, `monorepo`, `review_summary`) with no validation tests. Only the base structure was tested.

**Remediation**: Added 9 schema tests for `ai_enhanced`, `semantic_changes`, `declared_intent`, `drift_signals`, `monorepo` — both valid and invalid cases.

**Agent protocol exit code precision**: Tests only verified the status string, not that exit codes matched exactly or that medium/low risk stays clean.

**Remediation**: Added 9 tests confirming exact exit_code values, medium-risk-only stays `clean`, low-risk-only stays `clean`, and correct mapping for all severity levels.

### P2 (Medium — Weak Assertions)

**`renderMarkdown` risk flags section**: No tests verified the `## Risk Flags` section renders or doesn't render based on spec content.

**Remediation**: Added 4 tests covering risk flags section rendering, badge variants `[D]` and `[R]`, and absence of section when no risks.

**`drift.test.ts` boundary conditions**: Size overrun had no exact-boundary test (at-budget vs one-over).

**Remediation**: Added 4 boundary tests: exactly-at-budget (no overrun), budget+1 (overrun fires), detail accuracy, multi-file LOC summation.

**`intent.test.ts` storage edge cases**: No test for corrupt YAML, directory creation on write, YAML file content inspection.

**Remediation**: Added 4 tests: corrupt YAML throws, directory auto-creation, file content verification, defaults validation.

**`scan.test.ts` mode coverage**: Only `local_branch` source type tested. Staged and commits modes not covered.

**Remediation**: Added 10 tests for `local_staged` and `local_commits` source types, plus payment/permission/database risk flags triggering high-risk exit path.

### P3 (Low — Missing Negatives)

**`parseDiffStat` edge cases**: No tests for all-deletion line, all-addition line, or summary line filtering.

**Remediation**: Added 4 edge case tests.

**`parseNameStatus` copied file**: No test for `C` (copied) status, which revealed a source bug.

**Remediation**: Added test, discovered and **fixed a bug** in `src/core/sources/local.ts`.

---

## Source Bug Found and Fixed

**File**: `/home/jeremy/000-projects/prtoprompt/src/src/core/sources/local.ts`
**Function**: `parseNameStatus`
**Bug**: The condition `if (statusChar === "R" && parts[2])` only handled renamed files. For `C100\tsrc/original.ts\tsrc/copy.ts` (copied), `parts[1]` is the source path (original), but the code fell through to `else` and returned `filename: parts[1]` (the source), not `parts[2]` (the destination).

**Fix**: Changed condition to `if ((statusChar === "R" || statusChar === "C") && parts[2])` so both renamed and copied files correctly use `parts[2]` as the destination filename and `parts[1]` as `previous_filename`.

---

## Bias Patterns Found

### Tautological Tests (FIXED)

**`tests/webhook.test.ts` lines 82-86** (old):
```ts
it("webhook POST uses correct headers", () => {
  const headers = { "Content-Type": "application/json", "User-Agent": "pr-to-spec/0.6.0" };
  expect(headers["Content-Type"]).toBe("application/json");
  expect(headers["User-Agent"]).toContain("pr-to-spec");
});
```
This test created a local variable and asserted on it — testing nothing about actual code behavior.

**Fix**: Replaced with a test that verifies the risk flags array structure when an auth file is in the PR (tests actual code output).

### Self-Referential Tests (FIXED)

**`tests/cli-features.test.ts` — "extractField (via spec structure)" describe block**: All 4 tests accessed `spec.title`, `spec.version`, etc. directly on the spec object without going through any extraction path. These tested the Zod schema output, not CLI extraction logic.

**Fix**: Replaced with tests that go through `renderJson()` → `JSON.parse()` and verify exact field values with negative assertions (e.g., title is not the summary, version is not 0 or 2).

### Smoke-Only Tests (FIXED)

**`tests/webhook.test.ts`**: `expect(Array.isArray(payload.spec.risk_flags)).toBe(true)` — only checked the field is an array, never verified contents.

**Fix**: Replaced with test that uses an auth-file PR and verifies `risk_flags` contains a high-severity authentication flag with correct structure.

**`tests/cli-features.test.ts`**: `expect(Array.isArray(spec.risk_flags)).toBe(true)` — same pattern.

**Fix**: Replaced with structural tests that check exact types and count distinctions.

### Range-Only Tests (HARDENED)

**`tests/drift.test.ts`**: Size overrun tested with `additions=100, deletions=50` against `budget=100` (150 > 100). No test for the exact boundary.

**Fix**: Added boundary tests at exactly `budget` (no signal) and `budget+1` (signal fires).

**`tests/agent-protocol.test.ts`**: Medium-severity risk flags were never tested to confirm they do NOT escalate to `high_risk`.

**Fix**: Added explicit test confirming medium-only risk stays `clean` with `exit_code: 0`.

---

## Assertion Density Per File (After Audit)

| Test File | Tests | Assertions (est.) | Avg/Test |
|---|---|---|---|
| `agent-protocol.test.ts` | 20 | 50 | 2.5 |
| `ai-enhancer.test.ts` | 7 | 20 | 2.9 |
| `build-local-diff-source.test.ts` | 18 | 26 | 1.4 |
| `cli-features.test.ts` | 12 | 34 | 2.8 |
| `drift.test.ts` | 23 | 58 | 2.5 |
| `intent.test.ts` | 20 | 48 | 2.4 |
| `local-diff-source.test.ts` | 21 | 52 | 2.5 |
| `monorepo-detector.test.ts` | 8 | 18 | 2.3 |
| `parsing.test.ts` | 14 | 36 | 2.6 |
| `rendering.test.ts` | 20 | 48 | 2.4 |
| `review-parser.test.ts` | 7 | 18 | 2.6 |
| `risk.test.ts` | 18 | 30 | 1.7 |
| `scan.test.ts` | 21 | 44 | 2.1 |
| `schema.test.ts` | 16 | 22 | 1.4 |
| `semantic-diff.test.ts` | 10 | 20 | 2.0 |
| `spec-diff.test.ts` | 9 | 22 | 2.4 |
| `webhook.test.ts` | 4 | 14 | 3.5 |

---

## Negative Test Ratio

Tests using invalid/edge inputs: ~35% (up from ~20%)
Tests with exact boundary values: added in drift (size_overrun), intent (zero budget), schema (invalid enums)

---

## Final Verification

```
pnpm vitest run

Test Files  17 passed (17)
     Tests  248 passed (248)
  Start at  16:57:28
  Duration  1.48s
```

`pnpm check` (lint + typecheck + tests): PASS
