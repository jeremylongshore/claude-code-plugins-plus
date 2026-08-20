<!-- doc-class: record -->

# Epics 1–4 Verification Audit — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epics 1–4 closure records (AARs 774, 777, 789, 801)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Trigger:** Owner directive — "go over the so-called completed epics and beads in detail and
  make sure the work is really done"
- **Method:** Three parallel adversarial auditors, each instructed to REFUTE closure claims by
  executing gates, not by reading records. Verified at main `a9fb4a9f9`, clean tree.
- **Fixes:** PR #1291 (census gate), PR #1292 (stats token fail-red), plus the calibration PR
  that files this record

## Verdict

**The epics' bodies are real: 34 of 37 audited claims CONFIRMED by execution.** Three actionable
defects were found, none requiring an epic reopen (warden standard: record correction, not
reopen — the gates were delivered; one had a CI-blind spot, one residual had a silent fallback,
and several dated records carried stale numbers). All are dispositioned below.

## Auditor 1 — Epic 4 (14 beads): 14/14 CONFIRMED, 0 REFUTED

Every gate exists, is wired, and was **executed** with exit 0 during the audit: gitleaks shape
gate (10 documented exceptions, no blankets), safety ratchet (exact pinned counts),
MCP destructive-policy registry (14/14 plugins with both refusal tests PASS), denylist gate
(52 first-party denylist-bearing skills), plaintext pre-flight, dolt guard suite 6/6, python
suite 55/55. Strongest proof: the E4.7 push-leg ran green on a real main push (run
32314529648, step-level conclusions verified). 5/5 recent main CI runs success; required
contexts exactly {ci-required, gitleaks, skill-conform}; `compute_compliance_rate` confirmed
called at the report path, not dead code.

Two recorded observations (designed behavior, not refutations):

1. **`secret-diff-scan` passes vacuously on push events** — it is a PR-diff gate by design;
   weekly trufflehog covers main. A green badge on a main push run carries no scan signal for
   that leg. Reader guidance, not a defect.
2. **`enforce_admins: false` residual** is self-disclosed in the workflow, not fixed — the
   safety story still rests on an admin not overriding. Epic 7 territory per the blueprint.

## Auditor 2 — Epics 1–2: closure bodies CONFIRMED; 2 defects in the Epic 1 residual

All 12 doc-governance/supply-chain gates exist, are wired through `ci-required`, and exited 0
live. Both parent beads CLOSED with close reasons citing real merge SHAs that really add the
named AARs; every cited AAR number (730–776 range) exists on disk; Epic 2's fact-assertion
pins are live and green.

**REFUTED (residual, not epic body) — finding B:**

1. At audit time the daily-stats **schedule trigger had never completed green under
   `BOT_PR_TOKEN`**: the token secret was written 87 seconds before the first green (manual)
   run — i.e. materially **after** the Epic 1 closure record asserted it.
2. `update-npm-stats.yml` used `${{ secrets.BOT_PR_TOKEN || secrets.GITHUB_TOKEN }}` — a
   silent fallback. Token expiry would degrade to the zero-checks `GITHUB_TOKEN` path instead
   of failing red (that fallback is also why the pre-fix scheduled runs looked "green").

**Fix (merged):** PR #1292 — a first guard step fails RED with rotation instructions when
`BOT_PR_TOKEN` is absent/empty; both token sites lose the fallback; the network fetch steps
carry `timeout-minutes`.

**Schedule-trigger proof — ACHIEVED during remediation:** the 2026-08-20 00:27 UTC
**scheduled** run (32317409056) completed `success` in 30.4 minutes and opened PR #1290
authored by `jeremylongshore` — i.e. via the fine-grained PAT, whose PRs re-trigger required
checks (`ci-required` reported on #1290, which `github-actions[bot]` PRs cannot cause).

**Two corrections discovered while proving it:**

- **The "~29-minute hang" in the original audit finding was a mischaracterization.** A healthy
  fetch legitimately takes ~25–30 minutes: 423 candidates × 4 requests, deliberately serial at
  ~4 req/s to stay under npm's per-IP cap (the last 6 green runs: 29–35 min total). The
  cancelled scheduled run was killed by the next dispatch's concurrency group mid-normal-run,
  not stuck. Consequently the 10-minute fetch timeout merged in #1292 was miscalibrated and
  failed a healthy dispatch; the calibration PR raises it to 45 (fail-fast preserved vs the 6h
  job default). The same PR drops a silently-ignored positional argument in
  `fetch-npm-stats.mjs` (`collectStats(names, 4)` — options-object parameter, so concurrency
  was always 1; the code now says what runs).
- **The pipeline could open unmergeable PRs by construction:** the workflow hardcoded the PR
  title `📦 Daily npm download stats refresh`, which fails the `commit-scope-check`
  conventional-commit PR-title gate added after that title was chosen (observed on #1290).
  The calibration PR switches the generated title to
  `chore(marketplace-site): refresh daily npm download stats`; the live #1290 was retitled in
  place.

**Record drift (dated record, live checks correct):** AAR 777 states "**2** effective
authority claimants … **12** canonical-table links". Live after Epic 4's register
(000-docs/790) landed: **3 claimants / 13 links**, and the live test pins 13. Expected
growth — the pinned test moved with reality; the dated AAR did not, and should be read with
this addendum.

## Auditor 3 — Epic 3: 9/10 CONFIRMED, 1 REFUTED

Confirmed: canonical layer intact (closed-schema, adapters enum, README's kernel-proposal #90
citation); 4/5 gates green with two honestly-disclosed vacuous-today gates (vendor-literals
scans 0 files, thinness has 0 adapters — the closure AAR discloses both); the portability
withdrawal held (first-party corpus uniform; only mirror-owned claims remain); beads 11/11
CLOSED; kernel proposal #90 OPEN.

**REFUTED — finding A: `validate:model-id-classifier` was RED at HEAD (exit 1).** The
committed exclusion list (`schemas/canonical/v0/model-id-exclusions.json`, 393 handles) was
missing `claude-or1m` — **Epic 4's own epic bead broke Epic 3's gate** and nothing caught it,
because:

1. The census test self-skips in CI (`classify-model-ids.test.mjs` skips when the untracked
   `.beads/issues.jsonl` is absent — every CI checkout), so main's green carried no signal
   for this gate.
2. `validate:model-id-classifier` ran only the test file, never the classifier script — and
   the classifier always exited 0 (reporting tool, not a gate).

This drift class recurs with EVERY new epic bead, so the fix targets the class.

**Fix (merged):** PR #1291 — pins `claude-or1m` (live census 394); adds a CI-reachable
tracked-tree census (`unpinnedTrackedHandles()`: bead-handle-shaped tokens on bead-context
lines in tracked files must be pinned — new epic beads land in tracked AARs immediately, so
the drift now goes red in CI); adds `--check` gate mode and the two-step
`node --test … && node … --check` package.json shape used by the sibling gates; list
invariants (sorted, unique) assert always; a detection-path test proves the scan surfaces
real handles under an empty pin set (Greptile review finding, fixed in-flight). Hardening in
the same PR: `KNOWN_HARNESSES` moved to `scripts/lib/harness-lexicon.mjs` (single-owner lib
placement; both the portability and denylist gates import one definition).

## Counting-basis clarification — "2,700 claims withdrawn" (AAR 786)

The "2,700 first-party SKILL.md files" figure in AAR 786 is a **file-edit count across
duplicated trees**: roughly 1,456 are plugin skills and the remainder are curated-mirror /
sibling copies of the same skills. The earlier 1,454→2,700 "supersession" was a
**counting-basis change** (per-skill → per-file-copy), not a new round of discoveries. The
withdrawal itself is confirmed held — the first-party corpus is uniform — but AAR 786 should
be read with this basis note; it did not state it.

## Disposition summary

| Finding | Class                                                                        | Disposition                                                                            |
| ------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| A       | Epic 3 gate CI-blind + red at HEAD                                           | Fixed at root — PR #1291 (census CI-visible; gate has teeth; detection path tested)    |
| B       | Epic 1 residual: silent token fallback; schedule unproven                    | Fixed — PR #1292 + calibration PR; schedule proof achieved (run 32317409056, PR #1290) |
| C       | Record drifts (AAR 777 numbers; AAR 786 counting basis; Epic 4 observations) | This addendum is the correction record; no source edits to dated AARs                  |

No epic reopens: the warden standard applies — deliverables shipped and verified; corrections
are records, not rework. Correcting `bd note`s were placed on `claude-t9s9.4` (census drift +
fix), `claude-or1m` (its creation broke the census — cross-reference), and `claude-hz8f`
(stats schedule-proof achieved).

## Lessons

1. **A gate whose only drift detector reads untracked state is CI-theater.** The census
   "worked" on dev boxes and was structurally blind in CI. Every gate should have at least
   one leg that runs from tracked artifacts alone.
2. **`||` fallbacks on credentials convert failure into silent degradation.** If a credential
   is load-bearing, its absence must be red, not a quieter shade of green.
3. **Closure claims about scheduled automation need one completed run on the real trigger.**
   A manual dispatch is evidence of the code path, not of the schedule.
4. **Calibrate timeouts against measured healthy runtime, not against the incident.** The
   "29-minute hang" was a healthy run; the first corrective timeout re-broke the pipeline it
   meant to protect. Six green-run durations were the right baseline.
5. **Dated records drift by design; pinned tests move with reality.** The correction mechanism
   is an addendum record like this one, never a silent edit to a dated AAR.
