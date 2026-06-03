# THEORY — Why npm Dependency Audits Matter

## The shape of the problem

A modern Node application is mostly other people's code. A typical
React + Next.js app installs ~30 direct dependencies and ends up
with ~1,500 packages in `node_modules` after npm resolves the
transitive closure. Every one of those packages can:

1. Ship a known CVE that gets disclosed after you installed.
2. Be hijacked through maintainer-account takeover (the npm registry
   has had several published cases since 2017).
3. Be replaced by a typosquatted near-name package that someone
   slipped into a lockfile during a careless `npm install`.

Because npm packages execute arbitrary JavaScript on install
(`postinstall` scripts), a single compromised package in your
transitive tree can read environment variables, exfiltrate secrets,
and pivot to other systems with no user interaction beyond the
install.

## Historical npm supply-chain compromises

These are the cases that drove the industry to treat dependency
auditing as a CI gate, not optional polish.

| Year | Event | Mechanism |
|---|---|---|
| 2018 | `event-stream` | Maintainer transferred to a new account that injected wallet-stealing code into a transitive dep (`flatmap-stream`). Affected Bitcoin wallet users. |
| 2021 | `ua-parser-js` | Maintainer account compromise. Crypto miner shipped to ~8M weekly downloads. |
| 2022 | `node-ipc` | Maintainer-installed protestware that targeted users in specific geographies. |
| 2022 | `colors.js` / `faker.js` | Maintainer self-sabotage; broke production builds globally for the affected versions. |
| 2024 | `lottie-player` | Cloudflare CDN compromise distributed wallet-drainer code. |

Each case ended with the same remediation: roll back to a known-good
version range, audit logs for exploitation evidence, publish an
incident postmortem. The presence of an audit gate would not have
prevented the original install (the malicious code was new), but
would have surfaced the compromise within hours of disclosure.

## Direct vs transitive: the remediation diff

A CVE in a direct dependency you require in `package.json` is
fixable by upgrading the version range. A CVE in a transitive
dependency requires either (a) a parent bump that pulls in the fix
or (b) an `overrides` block in your root `package.json`.

The `overrides` mechanism was introduced in npm 8.3 (December 2021).
Before that, only Yarn's `resolutions` field offered the equivalent
escape hatch. `overrides` lets you force the resolved version of a
package regardless of what the dependency graph requested:

```json
{
  "overrides": {
    "minimist": "^1.2.6"
  }
}
```

This is safe when the override pins to a SemVer-compatible version
of the package the parent expected. It is RISKY when the override
crosses a major-version boundary — the parent may rely on removed
APIs and break at runtime. The audit script tags transitive findings
with a `relationship: transitive` evidence field to flag them for
the operator's manual review.

## npm audit output schema diff (v1 vs v2)

npm 6 emitted findings under an `advisories` key, one per advisory.
npm 7+ rewrote the output to a `vulnerabilities` key, keyed by
package name, with the per-package record summarizing all advisories
affecting that package.

| Aspect | v1 (npm 6) | v2 (npm 7+) |
|---|---|---|
| Top-level key | `advisories` | `vulnerabilities` |
| Keyed by | Advisory ID | Package name |
| Direct vs transitive | implicit | explicit via `via` field |
| Fix metadata | `patched_versions` string | `fixAvailable` object or boolean |
| CVE field | `cves` array | per-advisory `cve` field in `via[]` |

This skill's parser handles both shapes. Practically, most modern
projects run npm 8+; the v1 parser is kept for legacy CI runners
and engineering laptops that haven't upgraded.

## Why severity normalization matters

Different tools use different severity vocabularies. npm uses
`info/low/moderate/high/critical`. CVSS uses numeric scores.
GitHub uses 4 levels. PyPA uses something else again. The
penetration-tester `Severity` enum is the canonical mapping target
so downstream consumers (SOC2 evidence packages, security
dashboards, executive summary reports) see one vocabulary across
every tool. The `Severity.from_npm_audit` classmethod in
`lib/finding.py` does the npm-specific mapping.

## When `npm audit fix` is dangerous

`npm audit fix` rewrites `package-lock.json` to the closest
non-breaking versions that resolve advisories. Two failure modes:

1. **Semver-major fix required.** npm refuses to auto-apply and
   warns "requires manual review." This is correct behavior; do not
   pass `--force` casually. A major version bump can break the
   parent's API contract.
2. **Lockfile churn on shared CI runners.** If the lockfile rewrite
   happens in a CI step that doesn't commit back, the next CI run
   sees the same vulnerabilities and re-applies the fix, producing
   a stable but undocumented divergence between developer workstations
   and CI. Either commit the fix in CI (with appropriate guards) or
   require the fix to land via human PR.

## When to use the CISA KEV list

NIST's NVD scoring (CVSS) reflects intrinsic severity. CISA's Known
Exploited Vulnerabilities (KEV) catalog reflects observed exploitation
in the wild. A high-CVSS finding with no KEV listing is concerning;
a medium-CVSS finding WITH KEV listing is more concerning because
attackers are actively using it. The skill currently emits CVSS-derived
severity only; KEV enrichment is a planned addition via the
`mcp__pen-tester-cve` MCP server when wired.
