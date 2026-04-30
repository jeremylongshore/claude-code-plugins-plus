# ADR-263: Decline BDD/Gherkin — no non-engineer readership for scenarios

| Field        | Value                                                                              |
|--------------|------------------------------------------------------------------------------------|
| Status       | Accepted (decline)                                                                 |
| Date         | 2026-04-29                                                                         |
| Decider      | Jeremy Longshore (Tons of Skills / Intent Solutions)                               |
| Driver       | `/audit-tests` smoke run (2026-04-21), recommendation tracked as issue #590        |
| Supersedes   | —                                                                                  |
| Superseded by| —                                                                                  |
| Related      | #592 (audit-tests roadmap meta), #589 (RTM/PERSONAS/JOURNEYS — installed)          |

## Context

`/audit-tests` recommended scaffolding three `.feature` files with
Playwright-BDD glue:

- `marketplace/features/plugin-install.feature`
- `marketplace/features/plugin-authoring.feature`
- `marketplace/features/cli-user.feature`

…plus `playwright-bdd.config.ts`, per-feature step files, and hash-pinning via
`audit-harness init`.

The audit issue itself flags BDD as **P2, not P1**, and acknowledges the
right preconditions for value:

- "Non-engineers want to read and write test scenarios"
- "The business rules are genuinely separable from the UI code"
- "An external stakeholder needs to approve 'what ships' in plain English"

…then notes that for this repo: "the marketplace is engineer-authored and
engineer-consumed; the business rules are relatively thin; there is no
external stakeholder signing off features in Gherkin."

The audit's own assessment is the right one. This ADR records the decision
to act on that assessment instead of installing BDD anyway.

## Decision

**Decline. Use existing Playwright `test()` blocks; revisit when readership
exists.**

Do not install playwright-bdd. Do not create `marketplace/features/`,
step files, or the BDD config. Do not hash-pin Gherkin files we do not
have a non-engineer audience for.

This decision applies to **this repo only** — BDD is the right shape for
products with PM/QA/BA stakeholders writing or reviewing scenarios.

## Rationale

The senior-tech-lead read on this audit recommendation:

1. **BDD's value is non-engineer readership.** The whole point of Gherkin is
   that a PM, BA, or QA engineer can read a `.feature` file and say "yes,
   that's what we want to ship" or "no, that's wrong." If the only readers
   are engineers, Gherkin is a more verbose way to write a Playwright test —
   strictly more characters per scenario, with a translation layer (steps)
   to maintain. That is a net cost without a counterbalancing benefit.
2. **Existing Playwright tests already cover these flows.** The repo has
   T1–T9 dev tests (homepage search, search results, mobile viewport,
   install CTA, playbooks nav, explore flows, cowork page/integration) and
   P1–P8 production tests. The "plugin install" flow the audit proposes as
   a feature file is **already covered** by T4 (install CTA) and P1 (core
   page smoke tests). Adding a BDD layer would duplicate coverage in a
   different syntax, not add new coverage.
3. **The CLI flow does not need a feature file.** The audit proposes
   `cli-user.feature` covering `ccpi --version` and `ccpi --help`. The
   existing `cli-smoke-tests` job in `validate-plugins.yml` covers exactly
   this. Re-stating it as Gherkin produces zero new signal.
4. **The "plugin authoring" feature file would test the validator, not the
   product.** The audit proposes scenarios checking that
   `ccpi validate --strict` exits 0 on valid plugins and non-zero on
   invalid ones. That belongs in the validator's own test suite (or in
   `cli-smoke-tests`), not in a top-level `.feature` file. Putting validator
   tests in BDD form imposes the readership tax for tests no
   non-engineer will read.
5. **Hash-pinning Gherkin without a non-engineer reviewer is theater.** The
   audit issue notes "don't hash-pin until the features are reviewed by a
   non-engineer." If we don't have a non-engineer reviewer in the loop, the
   pin protects nothing — engineers edit, engineers re-pin, the
   constraint is loose by design.
6. **RTM / PERSONAS / JOURNEYS (#589) is the right primitive for this repo.**
   The persona-coverage and journey-mapping artifacts are engineer-readable
   traceability docs that pair Playwright tests to user flows without
   Gherkin's translation layer. We landed (or will land) those under a
   different track. They do the traceability work BDD would do, sized for
   our actual readership.

## Consequences

**Accepted:**
- The repo will not have `.feature` files. The `audit-tests` skill flags
  this as an absent layer, but the gap is visible at every audit, not silent.
- New contributors expecting Gherkin scenarios will find Playwright `test()`
  blocks instead. The codebase convention is "tests in TypeScript Playwright,
  trace to PERSONAS/JOURNEYS for the user-flow context."

**Mitigated:**
- The existing T1–T9 + P1–P8 Playwright test suite covers the same flows
  the audit proposed feature files for.
- `cli-smoke-tests` already exercises the CLI surface that
  `cli-user.feature` would have covered.
- RTM / PERSONAS / JOURNEYS (#589) provide engineer-readable user-flow
  traceability without Gherkin's overhead.

**Triggers to revisit (any one is enough):**
- A non-engineer (PM, BA, QA, customer-success lead) joins the team and
  needs to read or write product scenarios.
- A regulated or compliance-driven feature lands where an external auditor
  needs Gherkin-style behavior specs to sign off on "what shipped."
- A plugin-marketplace product surface emerges where the business rules
  separate cleanly from UI code and need stakeholder review (e.g., a
  paid-tier plugin gating mechanism with billing rules).
- The contributor base expands such that authoring/reviewing
  Playwright-in-TypeScript is a barrier to a stakeholder's review.

When any trigger fires, the install path is the one issue #590 already
documents. Re-open #590 (or open a successor) and reference this ADR.

## Alternatives considered

- **Install per the audit's recommendation.** Rejected: see Rationale.
- **Install playwright-bdd with one feature file** (the most consumer-facing
  flow, `plugin-install.feature`), as a "toe in the water." Rejected: even
  one `.feature` file requires the BDD config, the step glue infrastructure,
  the hash-pin, and the maintenance overhead. The cost floor is roughly the
  same whether you ship one feature or ten. Without a reader, even one is
  too many.
- **Convert existing Playwright tests to BDD.** Rejected: would force a
  syntax migration on a passing suite for zero added benefit. T1–T9 / P1–P8
  are working; rewriting them in Gherkin is purely additive cost.

## References

- Audit recommendation: GitHub issue #590
- Audit-tests roadmap meta-tracker: #592
- Existing Playwright suite: `marketplace/tests/T*.spec.ts` (dev) and
  `marketplace/tests/production/P*.spec.ts` (production)
- CLI smoke tests: `cli-smoke-tests` job in
  `.github/workflows/validate-plugins.yml`
- RTM / PERSONAS / JOURNEYS: `tests/RTM.md`, `tests/PERSONAS.md`,
  `tests/JOURNEYS.md` (landed under #589)
- `tests/TESTING.md` (`Installed gates` section will explicitly mark
  L6-bdd as deferred-by-ADR-263, not absent-by-oversight; existing
  Playwright suite remains the L6 implementation)
