# ADR-261: Defer dependency-cruiser architecture rules until policy is written

| Field        | Value                                                                              |
|--------------|------------------------------------------------------------------------------------|
| Status       | Accepted (decline)                                                                 |
| Date         | 2026-04-29                                                                         |
| Decider      | Jeremy Longshore (Tons of Skills / Intent Solutions)                               |
| Driver       | `/audit-tests` smoke run (2026-04-21), recommendation tracked as issue #586        |
| Supersedes   | —                                                                                  |
| Superseded by| —                                                                                  |
| Related      | #592 (audit-tests roadmap meta), #580 (audit-harness install)                      |

## Context

`/audit-tests` recommended installing `dependency-cruiser` to enforce
architectural rules (forbidden imports, no circular deps, no test files in
production, no cross-plugin imports) as fitness functions wired into CI and
hash-pinned via `audit-harness`.

The recommendation came with a fully-written `.dependency-cruiser.cjs` config
covering six rules:

- `no-cli-importing-marketplace`
- `no-marketplace-importing-cli`
- `no-cross-plugin-imports`
- `no-test-files-in-prod`
- `no-circular`
- `no-orphans` (warn-only)

Plus root scripts (`arch:check`, `arch:graph`), CI wiring, and a hash-pin
step.

## Decision

**Decline now. Write the architecture policy first, then revisit.**

Do not install `dependency-cruiser` at this time. Do not add the proposed
`.dependency-cruiser.cjs`, scripts, or CI step.

This decision applies to **this repo only** — `dependency-cruiser` is a
sound choice for repos with a written architecture policy that already
constrains imports.

## Rationale

The senior-tech-lead read on this audit recommendation:

1. **Architecture rules without a written policy create noise, not signal.**
   The proposed config encodes assumptions ("CLI must not import marketplace,"
   "MCP plugins must not cross-import") that have not been written down as a
   policy this repo subscribes to. If the rules pre-exist the policy, the
   first PR that hits a rule has no documented authority to point at — only
   a CI check that says "no." That breeds rule-bypass culture (`// dep-cruise
   ignore`) faster than it breeds compliance.
2. **Tools should follow policy, not generate it.** A reasonable order of
   operations is: write a one-page architecture-rules ADR documenting which
   imports are forbidden and why → land it on `main` → install
   `dependency-cruiser` to enforce it → hash-pin both. The opposite
   order — install the tool, draft rules to fill it — produces tooling for
   its own sake.
3. **Two of the rules in the proposed config are speculative for this repo.**
   `no-cli-importing-marketplace` and `no-marketplace-importing-cli` describe
   a separation that is already enforced by the package-manager policy
   (pnpm at root, npm in `marketplace/`). Encoding them in
   dependency-cruiser duplicates an existing gate. `no-cross-plugin-imports`
   is the most interesting candidate but needs the policy written first
   (under what conditions, if any, may shared utility code live across
   plugins?).
4. **`no-orphans` would generate hundreds of warnings on day one.** The
   `scripts/` tree alone has 70+ scripts that are run from CLI invocations
   and CI but are not "imported" anywhere. The rule needs a curated allow-list
   that we don't yet have. Shipping it now would mean either suppressing the
   warnings (training contributors to ignore the warning) or burning a
   sprint cleaning up flagged files we may not actually want to delete.
5. **Code review currently catches the cases the rules would catch.** The
   contributor base is small enough that a "do not import marketplace from
   the CLI" PR comment would land before merge. This is not a permanent
   answer; it is the right answer until the contributor base grows.

## Consequences

**Accepted:**
- The repo will rely on code review and the existing package-manager policy
  to prevent the import patterns dependency-cruiser would catch.
- A contributor could land an unintended cross-plugin import in code review;
  it would be caught by post-merge review or at the next audit, not at
  PR-open time.
- Circular dependencies, in particular, are not gated. If one is introduced,
  it would surface as a bundle-tree-shaking issue or a runtime "cannot
  read X of undefined" — a slower failure mode.

**Mitigated:**
- The `audit-tests` skill flags this as an absent layer, so the gap is
  visible at every audit.
- The package-manager policy gate (`scripts/check-package-manager.mjs`)
  already enforces the `pnpm` / `npm` boundary; it covers the highest-value
  case from the proposed config without dependency-cruiser overhead.

**Triggers to revisit (any one is enough):**
- An architecture-rules ADR is written and merged. At that point install
  dependency-cruiser to enforce it.
- A circular import causes a debugging incident.
- An unintended cross-plugin import lands and survives review.
- The contributor base expands beyond ~3 active engineers.
- A future audit shows architectural drift that code review missed.

When any trigger fires, the install path is the one issue #586 already
documents. Write the policy ADR first; install the tool to enforce it;
re-open #586 (or open a successor) and reference this ADR.

## Alternatives considered

- **Install per the audit's recommendation, then write policy after.**
  Rejected: rules-first-policy-second is the wrong order. Tools should
  enforce policy, not generate it.
- **Install only the `no-circular` rule** (the only universally-applicable
  rule in the proposed config). Marginal benefit, full toolchain cost.
  Reasonable as a future minimal-install if a circular import becomes a
  real-world incident.
- **Use ESLint's `no-restricted-imports`** instead of dependency-cruiser.
  Same problem (tool ahead of policy); ESLint is also far less expressive
  than dependency-cruiser for this class of rule.
- **Defer indefinitely.** Rejected: keeping a written ADR in `000-docs/`
  with explicit triggers gives a clean re-entry path; "defer indefinitely"
  is what the team does when nobody wrote it down.

## References

- Audit recommendation: GitHub issue #586
- Audit-tests roadmap meta-tracker: #592
- Existing package-manager gate: `scripts/check-package-manager.mjs` and
  `pnpm-workspace.yaml`
- `tests/TESTING.md` (`Installed gates` section will explicitly mark
  L3-arch as deferred-by-ADR-261, not absent-by-oversight)
