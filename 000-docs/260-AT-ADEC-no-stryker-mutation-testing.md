# ADR-260: Defer Stryker mutation testing for MCP plugin packages

| Field        | Value                                                                              |
|--------------|------------------------------------------------------------------------------------|
| Status       | Accepted (decline)                                                                 |
| Date         | 2026-04-29                                                                         |
| Decider      | Jeremy Longshore (Tons of Skills / Intent Solutions)                               |
| Driver       | `/audit-tests` smoke run (2026-04-21), recommendation tracked as issue #585        |
| Supersedes   | —                                                                                  |
| Superseded by| —                                                                                  |
| Related      | #592 (audit-tests roadmap meta), #583 (coverage thresholds — installed)            |

## Context

`/audit-tests` recommended installing Stryker mutation testing across the four
MCP plugin packages with vitest configs (`pr-to-spec`, `domain-memory-agent`,
`project-health-auditor`, `conversational-api-debugger`). The recommendation
was reasonable on its own merits — mutation testing answers a strictly
stronger question than coverage ("did the assertion verify behavior?" vs.
"was the line executed?") — and the audit's matrix marked it as P1 for
service/api packages.

The proposed install was substantial:

- Per-package `stryker.conf.json` with vitest runner + per-test coverage
  analysis
- Per-package `test:mutation` script in `package.json`
- Root `test:mutation:all` aggregator
- Weekly `mutation-test.yml` GitHub Actions workflow with 60-minute timeout,
  4-package matrix, artifact upload
- Per-module thresholds in `tests/TESTING.md`
- Hash-pinning the new policy via `audit-harness init`

Wall-clock cost on CI per run: approximately 5–20 minutes per package (the
overhead is roughly 5–15× the baseline test run, multiplied across four
packages even with concurrency).

## Decision

**Decline now. Revisit only when triggered by evidence.**

Do not install Stryker for the MCP plugin packages at this time. Do not add
the proposed weekly workflow, per-package configs, or thresholds in
`tests/TESTING.md`. The ratchet stays on coverage (#583) and the existing
vitest assertion suite.

This decision applies to **this repo only** — Stryker is a perfectly
reasonable choice for repos that meet the trigger criteria below.

## Rationale

The senior-tech-lead read on this audit recommendation:

1. **Mutation testing is most valuable when assertions are suspect.** Our
   MCP plugin tests are not the "happy-path-without-asserting" pattern that
   mutation testing is designed to catch. They use exact-match assertions
   on parsed output, and `pr-to-spec` in particular has 384 vitest tests
   that exercise schema validation, error paths, and edge cases. If those
   tests had no assertions, mutation would be the right alarm; they have
   assertions, so mutation here would mostly confirm what we already know.
2. **No regression has been caught (or missed) that mutation testing would
   have surfaced.** The signal we'd be paying for has not, to date, had
   detectable demand. We have not had a "tests passed but production broke"
   incident traceable to a non-asserting test. Adopting tooling for a
   demand that hasn't materialized creates carrying cost without obvious
   payback.
3. **CI minute and reviewer-attention budgets are real costs.** Five to
   twenty minutes per package per weekly run, plus dispatch overhead, plus
   investigating "survived" mutations in logging/telemetry code (the known
   noisy class). For a small contributor base, the per-finding investigation
   cost is high relative to the per-finding signal.
4. **Coverage thresholds (#583) are the load-bearing wall right now.** Until
   coverage is enforced and stable for at least one full release cycle,
   stacking mutation on top adds complexity without certainty that the
   underlying coverage signal is trustworthy. Stryker's own docs say the
   same: stand up coverage first, then mutation, not in parallel.

This is a "not yet" rather than "not ever." Mutation testing remains in the
toolkit; it just isn't paying for itself today.

## Consequences

**Accepted:**
- The repo will rely on coverage thresholds + assertion-grade tests as its
  unit-level safety net. Tests that "execute without asserting" can pass CI
  if a contributor writes them.
- We accept that some classes of regression — particularly silent mutations
  in arithmetic, comparison operators, and boolean expressions where the
  test only checks "did it return something?" — would not be caught.

**Mitigated:**
- Code review remains the human gate against the no-assertion test
  pattern. This is a small contributor base; the review pass is realistic.
- The `audit-tests` skill flags this as an absent layer, so the gap is
  visible at every audit, not silent.

**Triggers to revisit (any one is enough):**
- A regression incident traceable to a non-asserting unit test.
- The contributor base expands beyond ~3 active engineers (review can no
  longer be relied on for assertion-quality vetting).
- We add a security-critical or money-critical surface (auth, payments,
  cryptography) where the cost of a silent regression dominates the
  CI-minutes cost.
- A future audit shows coverage staying flat while bugs continue to ship —
  evidence that coverage alone has hit its useful ceiling.

When any trigger fires, the install path is the one issue #585 already
documents. Re-open #585 (or open a successor) and reference this ADR.

## Alternatives considered

- **Install per the audit's recommendation.** Rejected: see Rationale.
- **Install on a single highest-leverage package** (e.g. `pr-to-spec` only).
  Rejected for now: same ceiling on demand evidence; partial install creates
  asymmetric expectations across packages. Reasonable to revisit if a
  trigger above fires for one specific package.
- **Defer to a property-based testing layer instead** (fast-check, hypothesis).
  Tracked as a possible future, not in scope here. Property-based tests
  would address the "assertion-quality" question from a different angle and
  may be a better fit for some of the parsing-heavy modules.

## References

- Audit recommendation: GitHub issue #585
- Audit-tests roadmap meta-tracker: #592
- Coverage thresholds (the prerequisite that landed): #583
- `tests/TESTING.md` (`Installed gates` section will explicitly mark
  L3-mutation as deferred-by-ADR-260, not absent-by-oversight)
