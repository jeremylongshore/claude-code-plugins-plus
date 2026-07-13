---
name: performing-penetration-testing
description: |
  Orchestrate a penetration test by routing user intent to one or
  more of the 25 narrow skills in this pack. Confirms authorization
  + scope FIRST (cluster 5), runs the relevant scan skills (clusters
  1-4), then composes findings into the customer deliverables
  (cluster 6) plus an integrity-attestable engagement archive
  (cluster 5). Backward-compatible with v2 invocations — "pentest",
  "security scan", "audit dependencies" still work but now route to
  the narrow skills instead of the v2 monolithic scripts.
  Use when: starting a security engagement, running an ad-hoc
  scan, planning a multi-day pentest, or operating the full
  authorization-to-deliverable workflow end-to-end.
  Trigger with: "pentest", "security scan", "vulnerability
  check", "audit dependencies", "check headers", "find secrets",
  "OWASP scan", "security audit".
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash(python3:*)
  - Bash(pip:*)
  - Bash(npm:*)
  - Bash(bandit:*)
  - Bash(pip-audit:*)
  - Bash(pipdeptree:*)
  - Bash(gpg:*)
  - Bash(tar:*)
disallowed-tools:
  - Bash(rm:*)
  - Bash(curl:*)
  - Bash(wget:*)
  - Bash(nmap:*)
  - Bash(nikto:*)
  - Bash(sqlmap:*)
  - Write(.env)
  - Edit(.env)
version: 3.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code
tags:
  - security
  - testing
  - pentest
  - orchestration
---

# Performing Penetration Testing

## Overview

v3.0.0 of `penetration-tester` is a 25-skill pack. Each skill is
narrow and heavy-hitter compliant (≥250 LOC scripts, ≥2 reference
docs, 8-field SKILL.md frontmatter). This orchestrator routes
user intent to the right combination of narrow skills.

The 25 skills group into 7 clusters:

- **Cluster 0** — this orchestrator
- **Cluster 1 (5 skills)** — Network / transport
- **Cluster 2 (4 skills)** — Information disclosure
- **Cluster 3 (6 skills)** — Source-code static analysis
- **Cluster 4 (4 skills)** — Dependency analysis
- **Cluster 5 (3 skills)** — Engagement governance
- **Cluster 6 (3 skills)** — Reporting

Cluster 5 + 6 are the v3 additions versus v2. Cluster 5 runs
BEFORE any scan and refuses to proceed if authorization is
missing or scope is malformed. Cluster 6 runs AFTER scans and
produces the deliverable artifacts (vulnerability report, OWASP
coverage report, executive summary, chain-of-custody archive).

## Instructions

The orchestrator's job is intent routing — given a user utterance, decide which of the 25 narrow skills to invoke and in what order. Four steps:

### Step 1 — Parse the user intent

Match the utterance against the intent-routing table below. The leftmost matching row determines the routing. If no exact match, default to the cluster-1-4 governance-first sequence and pare back based on context.

### Step 2 — Run authorization-first

Before any cluster 1-4 scan invocation, run `confirming-pentest-authorization`. If it emits any CRITICAL finding, HALT — do not invoke any scan skill. The user must resolve the authorization issue before proceeding.

### Step 3 — Run the matched skills in order

Invoke each skill from the routing-table row, in the listed order. Each skill emits its findings as JSON/JSONL/markdown via `lib/report.py`. Persist per-skill output into `engagement/findings/<skill>-<date>.jsonl` so the cluster 6 skills can consume them.

### Step 4 — Compose deliverables

After scan skills complete, run cluster 6 in sequence: `mapping-findings-to-owasp-top10`, then `composing-vulnerability-report`, then `generating-executive-summary`, then `recording-pentest-engagement` for the chain-of-custody archive.

## Intent routing (the table)

| User intent / trigger phrase | Skills to invoke (in order) |
|---|---|
| "pentest", "full security scan" | confirming-pentest-authorization → defining-pentest-scope → cluster 1-4 (all) → mapping-findings-to-owasp-top10 → composing-vulnerability-report → generating-executive-summary → recording-pentest-engagement |
| "check headers" / "scan URL" | confirming-pentest-authorization → checking-http-security-headers + analyzing-tls-config + detecting-ssl-cert-issues |
| "CORS check" | confirming-pentest-authorization → auditing-cors-policy |
| "check SSL" / "certificate" | analyzing-tls-config + detecting-ssl-cert-issues |
| "audit npm dependencies" | auditing-npm-dependencies |
| "audit python dependencies" / "pip-audit" | auditing-python-dependencies |
| "find vulnerable deps" | auditing-npm-dependencies + auditing-python-dependencies + tracing-transitive-vulnerabilities |
| "license check" / "GPL contamination" | checking-license-compliance |
| "find hardcoded secrets" / "credential scan" | scanning-for-hardcoded-secrets |
| "SQL injection scan" | detecting-sql-injection-patterns |
| "command injection scan" | detecting-command-injection-patterns |
| "code audit" / "static analysis" | cluster 3 (all 6 skills) |
| "OWASP scan" / "OWASP coverage" | cluster 1-4 → mapping-findings-to-owasp-top10 |
| "confirm authorization" / "verify ROE" | confirming-pentest-authorization |
| "define scope" / "generate allowlist" | defining-pentest-scope |
| "write report" / "generate exec summary" | composing-vulnerability-report → generating-executive-summary |
| "archive engagement" / "chain of custody" | recording-pentest-engagement |

When unsure which to invoke, prefer the governance-first sequence
(authorization + scope) and add cluster-1-4 skills based on what
the user described.

## Full 25-skill index

### Cluster 0 — Orchestration

- `performing-penetration-testing` — this skill

### Cluster 1 — Network / transport (5)

- `analyzing-tls-config` — TLS protocol versions, cipher suites, HSTS
- `detecting-ssl-cert-issues` — cert validity, expiry, chain integrity
- `auditing-cors-policy` — origin reflection, credential bypass, wildcard
- `checking-http-security-headers` — CSP, HSTS, X-Frame-Options, etc.
- `probing-dangerous-http-methods` — TRACE, DELETE, PUT exposure

### Cluster 2 — Information disclosure (4)

- `detecting-exposed-secrets-files` — `.env`, `.git`, backup files
- `detecting-debug-endpoints` — `/server-status`, admin panels
- `fingerprinting-server-software` — Server-header version exposure
- `detecting-directory-listing` — Apache/nginx autoindex

### Cluster 3 — Source-code static analysis (6)

- `scanning-for-hardcoded-secrets` — AWS / GitHub / Stripe / Slack / API keys
- `detecting-sql-injection-patterns` — string-concat SQL, unsanitized input
- `detecting-command-injection-patterns` — shell exec with user input
- `detecting-eval-exec-usage` — eval/exec with dynamic content
- `detecting-insecure-deserialization` — pickle/yaml.load/Marshal use
- `detecting-weak-cryptography` — MD5/SHA1/DES, hardcoded IVs, ECB mode

### Cluster 4 — Dependency analysis (4)

- `auditing-npm-dependencies` — `npm audit` wrapper with v1/v2 parsers
- `auditing-python-dependencies` — `pip-audit` wrapper with OSV scoring
- `checking-license-compliance` — SPDX classification + copyleft contamination
- `tracing-transitive-vulnerabilities` — dep-graph leverage analysis

### Cluster 5 — Engagement governance (3, new in v3)

- `confirming-pentest-authorization` — Rules of Engagement validation
- `defining-pentest-scope` — target enumeration + IP allowlist
- `recording-pentest-engagement` — SHA-256 manifest + GPG signing

### Cluster 6 — Reporting (3, new in v3)

- `composing-vulnerability-report` — unified deliverable report
- `mapping-findings-to-owasp-top10` — A0X classification + coverage rollup
- `generating-executive-summary` — 0-100 risk score + top-3 priorities

## End-to-end workflow

For a typical engagement, the orchestrator routes through:

```
                  +----------------------------------+
                  | confirming-pentest-authorization |
                  +-------------+--------------------+
                                | (CRITICAL halts here)
                                v
                  +----------------------------------+
                  | defining-pentest-scope            |
                  +-------------+--------------------+
                                |
                                v
   +-------------+-------------+-------------+-------------+
   | Cluster 1   | Cluster 2   | Cluster 3   | Cluster 4   |
   | (5 skills)  | (4 skills)  | (6 skills)  | (4 skills)  |
   +-------------+-------------+-------------+-------------+
                                |
                                v
                  +----------------------------------+
                  | mapping-findings-to-owasp-top10   |
                  +-------------+--------------------+
                                |
                                v
                  +----------------------------------+
                  | composing-vulnerability-report    |
                  +-------------+--------------------+
                                |
                                v
                  +----------------------------------+
                  | generating-executive-summary      |
                  +-------------+--------------------+
                                |
                                v
                  +----------------------------------+
                  | recording-pentest-engagement      |
                  +----------------------------------+
```

## Backward compatibility

The v2 monolithic scripts (`security_scanner.py`,
`dependency_auditor.py`, `code_security_scanner.py`) remain in
`scripts/` as the underlying engine for the original v2
invocation patterns. The v3 narrow skills re-implement and
extend that logic with the canonical `lib/finding.py` schema and
the shared `lib/report.py` output module.

If a downstream user has scripted invocations of the v2 scripts,
those still work. New work should use the narrow skills directly.

The orchestrator's old "Step 1 / Step 2 / Step 3" instructions
in v2 are subsumed by the intent-routing table above. The v2
checks correspond to:

| v2 invocation | v3 equivalent |
|---|---|
| `security_scanner.py URL --checks headers` | `checking-http-security-headers` |
| `security_scanner.py URL --checks ssl` | `analyzing-tls-config` + `detecting-ssl-cert-issues` |
| `security_scanner.py URL --checks cors` | `auditing-cors-policy` |
| `security_scanner.py URL --checks endpoints` | `detecting-exposed-secrets-files` + `detecting-debug-endpoints` |
| `security_scanner.py URL --checks methods` | `probing-dangerous-http-methods` |
| `dependency_auditor.py DIR --scanners npm` | `auditing-npm-dependencies` |
| `dependency_auditor.py DIR --scanners pip` | `auditing-python-dependencies` |
| `code_security_scanner.py DIR --tools regex` | cluster 3 skills (per pattern type) |
| `code_security_scanner.py DIR --tools bandit` | cluster 3 skills (bandit pattern subset) |

## Prerequisites

Per-skill prerequisites are documented in each skill's
`SKILL.md`. The shared module `lib/` requires Python 3.9+ and
the standard library only.

Optional tools used by individual skills:

- `bandit` (Python static-analysis backend, cluster 3)
- `pip-audit` (cluster 4 Python dependency audit)
- `pipdeptree` (cluster 4 transitive trace)
- `gpg` (cluster 5 evidence signing)
- `npm` (cluster 4 npm dependency audit)

Each skill emits a graceful INFO Finding when an optional
dependency is missing and falls back to a degraded but functional
mode where possible.

## Authorization is non-negotiable

The orchestrator REFUSES to invoke cluster 1-4 skills until
`confirming-pentest-authorization` has emitted no CRITICAL or
HIGH findings against the ROE. The cost of running an authorized
scan is delay until the ROE is verified. The cost of running an
unauthorized scan is potential criminal liability under CFAA
(US), Computer Misuse Act (UK), or equivalent foreign statutes.

For details on the legal framework + ROE structure, see
`confirming-pentest-authorization/references/THEORY.md`.

## Examples

### Example 1 — Full engagement, end to end

```
User: "Run a full pentest on engagements/acme-2026-q2/"
```

Orchestrator routes:

1. `confirming-pentest-authorization --roe engagements/acme-2026-q2/roe.yaml`
2. (if no CRITICAL findings) `defining-pentest-scope --roe engagements/acme-2026-q2/roe.yaml`
3. Cluster 1-4 skills against each in-scope target, emitting per-skill JSONLs into `engagements/acme-2026-q2/findings/`
4. `mapping-findings-to-owasp-top10 engagements/acme-2026-q2/`
5. `composing-vulnerability-report engagements/acme-2026-q2/`
6. `generating-executive-summary engagements/acme-2026-q2/`
7. `recording-pentest-engagement engagements/acme-2026-q2/ --sign --tar ...`

### Example 2 — Ad-hoc header check

```
User: "Check security headers on https://app.acme.example"
```

Orchestrator routes:

1. `confirming-pentest-authorization` (operator must confirm authz; fast path for own-system testing)
2. `checking-http-security-headers https://app.acme.example`

### Example 3 — Dependency audit

```
User: "Audit dependencies in /path/to/project"
```

Orchestrator routes:

1. `auditing-npm-dependencies /path/to/project` (if `package.json` present)
2. `auditing-python-dependencies /path/to/project` (if Python project present)
3. (if either produced HIGH/CRITICAL findings) `tracing-transitive-vulnerabilities /path/to/project --audit-input <previous output>`

## Output

The orchestrator's output is the COMPOSITION of the called skills'
outputs. The canonical end-state deliverables of a full engagement:

- `engagement/findings/all-with-owasp.jsonl` — enriched unified findings
- `engagement/reports/vulnerability-report.md` — deep technical report
- `engagement/reports/owasp-coverage.md` — OWASP A0X rollup
- `engagement/reports/executive-summary.md` — C-level / board summary
- `engagement/manifest.sha256` (+ optional `.asc`) — chain-of-custody manifest
- `engagement/<archive>.tar.gz` — portable archive

## Error Handling

The orchestrator delegates error handling to each invoked skill.
Cluster 5 errors (missing ROE, missing scope) HALT the engagement.
Cluster 1-4 errors (scanner missing, network unreachable) emit
INFO findings and continue. Cluster 6 errors (missing source
findings) emit HIGH operational findings and continue with a
partial deliverable.

## Resources

- `references/OWASP_TOP_10.md` — OWASP Top 10 risks (legacy v2
  reference; the canonical OWASP table is now in
  `mapping-findings-to-owasp-top10/references/THEORY.md`)
- `references/SECURITY_HEADERS.md` — HTTP security header
  implementation guide
- `references/REMEDIATION_PLAYBOOK.md` — copy-paste fix templates
- Per-skill `THEORY.md` + `PLAYBOOK.md` files under each
  `skills/<skill-name>/references/`

## v3.0.0 release notes

Released 2026-06-03. Major changes:

- 25 narrow heavy-hitter skills replace the v2 3-script monolith
- New cluster 5 (engagement governance) and cluster 6 (reporting)
- Canonical `lib/finding.py` + `lib/report.py` schema across all skills
- `disallowed-tools` defense-in-depth for high-risk patterns (rm, curl, wget, .env edits)
- v2 scripts (`security_scanner.py`, `dependency_auditor.py`,
  `code_security_scanner.py`) preserved as backward-compatible
  scripts under `scripts/`

Migration: existing v2 invocations continue to work. New work
should use the narrow skills directly. See the backward-compat
table above for the v2 → v3 mapping.
