# ADR-262: Decline Semgrep — redundant against existing CodeQL + gitleaks + trufflehog stack

| Field        | Value                                                                              |
|--------------|------------------------------------------------------------------------------------|
| Status       | Accepted (decline)                                                                 |
| Date         | 2026-04-29                                                                         |
| Decider      | Jeremy Longshore (Tons of Skills / Intent Solutions)                               |
| Driver       | `/audit-tests` smoke run (2026-04-21), recommendation tracked as issue #587        |
| Supersedes   | —                                                                                  |
| Superseded by| —                                                                                  |
| Related      | #592 (audit-tests roadmap meta), NLPM external audit response (2026-04-21)         |

## Context

`/audit-tests` recommended adding Semgrep SAST plus Bandit (Python SAST) to
complement the existing CodeQL workflow, plus re-enabling the
`security-audit.yml` cron so `pnpm audit` runs weekly with
`--audit-level high`.

The proposed install was substantial:

- New `.github/workflows/semgrep.yml` running on PR, push, weekly cron, and
  manual dispatch — with a wide ruleset (`p/ci`, `p/security-audit`,
  `p/nodejs`, `p/typescript`, `p/python`, `p/owasp-top-ten`, `p/secrets`,
  `p/supply-chain`)
- New `.github/workflows/python-sast.yml` running Bandit on every Python
  change
- New `.semgrep/mcp-plugins.yml` with two custom rules (`mcp-no-raw-exec`,
  `mcp-plugin-json-required-fields`)
- Re-enable `security-audit.yml` cron and tighten `pnpm audit` to fail on
  high severity

This is genuinely valuable on a repo with no SAST. **But this repo already
has a substantial security stack**, hardened during the NLPM external audit
response on 2026-04-21:

- **CodeQL** for JavaScript/TypeScript + Python (`.github/workflows/codeql.yml`)
- **gitleaks** on every PR and push (`.github/workflows/secret-scan.yml`)
- **trufflehog** weekly verified-secrets scan (`.github/workflows/secret-scan.yml`)
- **`pnpm audit`** wired to dependency changes (in `security-audit.yml`)
- **Validator-driven** dangerous-pattern, suspicious-URL, and credential-shape
  scans (in `validate-plugins.yml` — `Security scan - Dangerous patterns`,
  `Security scan - Suspicious URLs`, `Security scan - Informational sweep`)
- **Plugin-level** `npm audit` per MCP plugin (in `validate-plugins.yml`)

The question is not "should we have SAST?" — we have it. The question is
"does layering Semgrep on top yield meaningfully more catches than the
existing stack already provides?"

## Decision

**Decline. Existing security stack is sufficient until evidence of a gap.**

Do not add `.github/workflows/semgrep.yml`, `.github/workflows/python-sast.yml`,
or `.semgrep/`. Do not duplicate the `pnpm audit` cron in `security-audit.yml`.

This decision applies to **this repo only** — Semgrep is a perfectly
reasonable choice for repos that don't already have CodeQL + gitleaks +
trufflehog covering the same ground.

## Rationale

The senior-tech-lead read on this audit recommendation:

1. **CodeQL and Semgrep overlap at the OSS level we'd actually run.** The
   audit issue acknowledges this directly ("CodeQL and Semgrep overlap but
   are not redundant"), then stacks both anyway. The pitched differentiation
   is "Semgrep is faster and has community rules" — but the speed argument
   is moot when CodeQL already runs in our CI without blocking PRs, and the
   community-rules argument matters most when we have specific custom
   patterns to enforce. We do not currently have a documented set of
   repo-specific SAST rules that CodeQL is missing. Without that list, we'd
   be adopting Semgrep on a hope-it-finds-something basis.
2. **Secret scanning is comprehensively covered.** The NLPM external audit
   on 2026-04-21 hardened our secret-scanning surface (gitleaks PR-and-push,
   trufflehog weekly verified). Adding Semgrep `p/secrets` on top duplicates
   coverage and produces parallel findings that have to be reconciled
   manually.
3. **Bandit on the Python tree would generate noise without payback.**
   The Python code in this repo is concentrated in `scripts/` (CI helpers,
   validators, freshie inventory) and `freshie/scripts/`. These are
   trusted-author scripts, not user-input handlers. Bandit's strongest
   findings target shell-out, deserialization, and crypto-misuse patterns —
   none of which match what our Python scripts do. The expected
   signal-to-noise ratio is low.
4. **Custom Semgrep rules require maintenance.** The proposed
   `mcp-no-raw-exec` and `mcp-plugin-json-required-fields` rules are real
   ideas, but the second one duplicates a check the existing universal
   validator already performs (`scripts/validate-skills-schema.py` enforces
   `plugin.json` allowed fields). Maintaining the same constraint in two
   places (validator + Semgrep) is exactly the kind of duplication that
   produces drift — a future contributor edits the validator and not the
   Semgrep rule, or vice versa, and now the policy is ambiguous.
5. **`pnpm audit` cron and `--audit-level high`** *is* a reasonable change
   from the audit issue and worth applying — but as a **separate** small
   PR scoped to `security-audit.yml`, not as part of a Semgrep install.
   Treat that as a follow-up; do not bundle it under the Semgrep
   recommendation.

This is not "we don't need SAST" — we have SAST. It's "we don't need
*more* SAST until evidence shows the existing layer is missing something."

## Consequences

**Accepted:**
- The repo will not run Semgrep. Some classes of OWASP Top 10 patterns that
  CodeQL's queries don't surface might go uncaught.
- The Python tree will not run Bandit. If a contributor adds a deserialization
  call or shell-out without review, it is not gated by a SAST tool — only by
  code review and the validator's `Security scan - Dangerous patterns`
  step.
- Custom MCP-plugin rules (the two proposed) are not enforced in CI. The
  `mcp-no-raw-exec` rule in particular is worth re-considering as a focused
  addition (see Triggers below).

**Mitigated:**
- CodeQL covers JavaScript / TypeScript / Python at the depth-of-analysis
  level Semgrep OSS does not match.
- gitleaks + trufflehog cover the secret-scanning gap explicitly.
- The validator's `Security scan - Dangerous patterns` step in
  `validate-plugins.yml` catches `rm -rf /`, `eval(`, IP-address-curl, and
  `base64 -d` patterns at PR time.
- The `audit-tests` skill flags this as an absent layer, so the gap is
  visible at every audit.

**Follow-up (separate PR, not blocked by this ADR):**
- Re-enable the `security-audit.yml` cron (currently commented out).
- Tighten `pnpm audit || true` to `pnpm audit --audit-level high`. This is
  a worthwhile bug fix on its own; track separately as a small PR.

**Triggers to revisit (any one is enough):**
- A specific class of vulnerability lands that CodeQL did not catch and
  Semgrep would have. (Concrete evidence of a gap, not speculation.)
- A custom MCP-plugin pattern emerges that the validator can't express but
  Semgrep can — e.g., a taint-tracking question across two files. At that
  point a focused, repo-specific Semgrep install (custom rules only, no
  community packs) is the right shape, not the broad-stroke install the
  issue proposes.
- The Python tree grows beyond utility scripts to include user-input or
  network-handling code. Bandit becomes appropriate.
- A regulatory or compliance requirement names Semgrep specifically.

When any trigger fires, scope the re-introduction to the specific gap,
not the full eight-pack the audit recommended.

## Alternatives considered

- **Install per the audit's recommendation.** Rejected: see Rationale.
- **Install Semgrep with custom rules only** (skip the community packs).
  Reasonable as a focused future install if a specific gap appears. Not
  the right shape today because we do not yet have a documented list of
  rules to enforce.
- **Replace CodeQL with Semgrep.** Rejected: CodeQL has deeper interprocedural
  taint analysis and is integrated with GitHub Advanced Security. We get
  more for our minute on CodeQL than on Semgrep at the OSS level.
- **Add only Bandit for Python.** Rejected for now: low expected
  signal-to-noise on this repo's Python tree. Reconsider if the Python
  surface area changes shape.

## References

- Audit recommendation: GitHub issue #587
- Audit-tests roadmap meta-tracker: #592
- NLPM audit response (auto-memory): `project_nlpm_audit.md` —
  documented the existing gitleaks + trufflehog hardening
- Existing security workflows:
  - `.github/workflows/codeql.yml`
  - `.github/workflows/secret-scan.yml` (gitleaks + trufflehog)
  - `.github/workflows/security-audit.yml` (pnpm audit, cron disabled)
  - `.github/workflows/validate-plugins.yml` (dangerous-patterns,
    suspicious-URLs, credential-shapes, npm audit per plugin)
- `tests/TESTING.md` (`Installed gates` section will explicitly mark
  L5-sec as covered-by-CodeQL+gitleaks+trufflehog,
  Semgrep-deferred-by-ADR-262)
