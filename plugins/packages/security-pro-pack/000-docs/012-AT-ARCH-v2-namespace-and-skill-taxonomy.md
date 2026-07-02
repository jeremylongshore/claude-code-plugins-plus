---
filing_code: AT-ARCH-SECURITY-PACK-V2-NAMESPACE-AND-SKILL-TAXONOMY-2026-07-02
date: 2026-07-02
status: locked
scope: plugins/packages/security-pro-pack (v2 umbrella) + naming boundary with the 3 HEAVY individual promotions
inputs:
  - 000-docs/684-AT-PLAN-security-pack-option-c-uplift.md (execution plan)
  - 000-docs/685-AT-ADEC-security-pack-option-c-scope.md (LOCKED scope — Option C)
  - 000-docs/686-AT-ADEC-security-pack-v1-deprecation-lane.md (LOCKED deprecation mechanics + the itemized 23-plugin absorption list)
  - 000-docs/687-AT-ADEC-security-pack-mcp-server-boundary.md (LOCKED shared-MCP tool set + layout)
  - plugins/packages/security-pro-pack/000-docs/011-DR-PAIN-catalog-master.md (pain-catalog schema + curation distribution)
  - Precedent: plugins/security/penetration-tester v3.0.0 (shipped heavy-hitter, 26 skill dirs), plugins/saas-packs/databricks-pack (v2 first-principles rebuild per its 000-docs/007-AT-ADEC), plugins/saas-packs/langchain-py-pack
affects: security-pro-pack v2.0.0 skill set, the v1-to-v2 migration table (Phase 2.1), shared MCP wiring (Phase 2.3), deprecation-lane re-anchor (686)
---

# Security-Pro-Pack v2 — Namespace and Skill Taxonomy

This document locks the two decisions delegated by AT-ADEC 685 to the Phase 2.2 design bead: (1) the v2 skill
naming convention and directory namespace, and (2) the first-principles skill taxonomy that absorbs all 23
LIGHT/PROMPT-ONLY v1 plugins. Scope, deprecation mechanics, and MCP boundary are NOT re-decided here — they are
locked in 685/686/687 and implemented as-is.

## 1. Namespace decision — `secpro-*`, flat `skills/` directory

**Locked:** every umbrella skill is named `secpro-<job>` in kebab-case and lives flat at
`skills/secpro-<job>/SKILL.md`. No domain subdirectories.

**Why `secpro-*` and not `security-*`:**

1. **Umbrella-pack precedent.** Both shipped heavy-hitter packs prefix every skill with the pack brand:
   `databricks-*` (24 skills) and `langchain-*` (33 skills). The pack brand here is `security-pro-pack`;
   `secpro-` is its compact, collision-free token.
2. **`security-*` is ambient, not a namespace.** Other plugins already own `security-*`-shaped names
   (`databricks-security-basics`, `langchain-security-basics`), and 5 of the 23 absorbed v1 plugins themselves
   start with `security-` — a `security-*` prefix would make the v1-name → v2-skill migration table ambiguous
   at a glance. `secpro-*` is unmistakably "the umbrella's skill."
3. **Budget.** The skill `name` field caps at 64 chars; a 7-char prefix leaves room for descriptive job names.

**Why flat, not `skills/<domain>/<skill>`:** 684 (a DRAFT plan) sketched domain subdirectories and 686's
migration-table *example rows* used nested paths — but namespace design was explicitly delegated to this bead,
and all three shipped precedents (penetration-tester v3, databricks-pack, langchain-py-pack) use flat
`skills/<name>/SKILL.md`, which is what marketplace skill discovery and the validators are built around. The
domain lives in the name (`secpro-injection-defense`), not the path. The Phase 2.1 migration table uses the
locked names below, superseding 686's illustrative nested paths.

**Boundary with the 3 HEAVY individual plugins:** they keep the penetration-tester v3.0.0 convention —
unprefixed gerund skill names (`analyzing-tls-config`, `detecting-sql-injection-patterns`) inside their own
plugin directories. Pack-prefix is the *umbrella* convention only. The functional boundary rule: **heavy-hitters
own detection/scanning mechanics; umbrella skills own defense, governance, and audit-facing jobs.** An umbrella
skill never duplicates a heavy-hitter's ground; it consumes findings and drives remediation/compliance.

## 2. Skill taxonomy — 12 skills absorb all 23 v1 plugins

The 23 absorbed plugins (itemized in 686: 12 LIGHT including the legacy security-pro-pack v1 itself, 11
PROMPT-ONLY) cluster into 12 first-principles skills. Per the databricks-v2 doctrine (007-AT-ADEC: 24 skills →
5, every pain covered, no fluff): fewer, deeper, pain-grounded skills — not 1:1 wrappers. 12 sits inside the
planned 8–14 band; the extra width vs databricks' 5 reflects that security spans disjoint practitioner jobs
(auditor, appsec engineer, IR lead) rather than one platform's ops surface.

Pain-domain column uses the catalog's locked curation distribution (011: ~40% credentials/auth, ~25%
injection/input-validation, ~15% misconfiguration, ~10% supply-chain, ~10% other) plus the research docs
(001–010) each skill draws from. MCP column lists the 687 v0.1.0 tools each skill leans on (v0.2.0+ tools noted
where relevant but never load-bearing for v2.0.0).

| # | v2 skill | One-line scope | Absorbs (v1) | Pain domains / research docs | Shared-MCP tools (687) |
|---|---|---|---|---|---|
| 1 | `secpro-framework-gap-audit` | Multi-framework control-gap assessment (SOC2, PCI DSS v4, HIPAA SR, GDPR Art. 32, NIST/ISO) with per-control evidence checklist | `soc2-audit-helper`, `pci-dss-validator`, `hipaa-compliance-checker`, `gdpr-compliance-scanner`, `compliance-checker` (devops/) | other/compliance; docs 001, 003, 007, 008, 009, 010 | `control_crosswalk`, `framework_list_controls` |
| 2 | `secpro-audit-reporting` | Compose auditor- and exec-readable deliverables from findings: evidence packaging, control mapping, remediation narrative | `compliance-report-generator`, `security-audit-reporter` | other/compliance; docs 001, 010 | `control_crosswalk` |
| 3 | `secpro-access-review` | Access-control governance: RBAC/least-privilege review, account lifecycle, periodic recertification | `access-control-auditor` | credentials/auth (~40% bucket); docs 003, 006, 010 | `framework_list_controls` (AC family), `control_crosswalk` |
| 4 | `secpro-session-hardening` | Browser session-layer defense: session management, cookie flags, CSRF token wiring and verification | `session-security-checker`, `csrf-protection-validator` | credentials/auth; docs 002, 006 | `owasp_top10_get`, `cve_search` |
| 5 | `secpro-injection-defense` | Remediate injection classes (SQLi, XSS) — input-validation posture, encoding/CSP wiring, fix verification | `sql-injection-detector`, `xss-vulnerability-scanner` | injection (~25% bucket); docs 002, 004 | `owasp_top10_get`, `cve_search`, `attack_pattern_lookup` |
| 6 | `secpro-data-protection` | Sensitive-data posture: secrets lifecycle/rotation, encryption at rest/in transit, PII exposure mapping | `secret-scanner`, `encryption-tool`, `data-privacy-scanner` | credentials/auth + other; docs 007, 008, 009 | `cve_search`, `control_crosswalk` (SC family); v0.2.0+: `osv_lookup` |
| 7 | `secpro-certificate-ops` | TLS/SSL certificate lifecycle: issuance, renewal, rotation, chain validation, expiry monitoring | `ssl-certificate-manager` | misconfiguration (~15% bucket); docs 004, 007 | `cve_search`; v0.2.0+: `kev_check` |
| 8 | `secpro-api-hardening` | API-surface security posture: per-endpoint authz, rate limiting, schema validation, OWASP API Top 10 alignment | `api-security-scanner` (api-development/) | injection + misconfiguration; docs 002, 005 | `owasp_top10_get`, `attack_pattern_lookup`, `cve_search` |
| 9 | `secpro-misconfig-sweep` | Config-posture review across app + infra: headers, debug endpoints, defaults, cloud misconfig classes | `security-misconfiguration-finder` | misconfiguration; docs 004, 006 | `attack_pattern_lookup`, `cve_search`; v0.2.0+: `kev_check` |
| 10 | `secpro-vulnerability-triage` | Findings triage and prioritization across any scanner output: CVSS/KEV-aware severity, dedupe, remediation SLAs | `vulnerability-scanner` (security/), `severity1-marketplace` (severity-classify lane) | supply-chain (~10% bucket) + all; doc 004 | `cve_lookup`, `cve_search`, `attack_pattern_lookup`; v0.2.0+: `epss_score`, `kev_check`, `osv_lookup` |
| 11 | `secpro-incident-runbook` | Incident response end-to-end: detection triage, containment, comms, post-incident review | `security-incident-responder` | other; docs 004, 005 | `attack_pattern_lookup`, `cve_lookup`; v0.2.0+: `kev_check` |
| 12 | `secpro-owasp-alignment` | Whole-posture OWASP Top 10 assessment: map an application to categories, gap list, remediation plan | `owasp-compliance-checker`, `security-pro-pack` v1 (`performing-security-audits`) | injection + misconfiguration; docs 002, 004 | `owasp_top10_get`, `control_crosswalk` |

**Absorption check:** 5+2+1+2+2+3+1+1+1+2+1+2 = 23. Every plugin on 686's list has exactly one destination
skill; no pain dropped (the databricks-v2 coverage rule).

**Clustering notes:**

- Skills 3–6 carry the ~40% credentials/auth pain weight across three distinct practitioner jobs (governance
  review, web-session defense, data protection) — merging them would recreate the v1 "capability prose" failure
  the pain catalog exists to prevent.
- Single-absorption skills (3, 7, 8, 9, 11) are not wrappers: each replaces a 0–199 LOC prompt with a
  research-anchored, MCP-wired, script-backed skill built to the 13-point bar. The v1 plugin is the *seed pain*,
  not the spec.
- `severity1-marketplace` follows 686's edge-case lane: its severity-classification capability lands in
  `secpro-vulnerability-triage`; its `prompt-improver` skill has **no direct successor** (686 permits
  "no-direct-replacement" rows). Final call in the Phase 2.1 inventory bead `claude-43pk`.
- The 4 SUBSTANTIAL plugins (`cors-policy-validator`, `database-audit-logger`, `security-headers-analyzer`,
  `input-validation-scanner`) are **not absorbed** (685 default: separate plugins under the umbrella). If
  Phase 2.1 folds any in, the reserved fold-in points are: cors → 4 or 8, headers → 9, input-validation → 5,
  audit-logger → 2 or 10.

## 3. The 3 HEAVY promotions (individual plugins, heavy-hitter standard)

**`penetration-tester` — already promoted.** Shipped at v3.0.0: 26 flat gerund-named skill dirs, each with
`SKILL.md` + `references/` + `scripts/`, engagement governance, OWASP mapping, and a 176-test pytest harness
(PR #837). It is the layout and naming precedent this document generalizes from. Remaining Option C work is
only the shared-MCP wire (684 Phase 1.7) once the 687 server ships — no restructure.

**`dependency-checker` — promotion outline.** Stays its own plugin at `plugins/security/dependency-checker`.
Expand the single `analyzing-dependencies` skill (1,570 LOC base: `dependency_check.sh`,
`vulnerability_report_parser.py`, `license_compliance_checker.py`) into gerund-named skills covering lockfile
forensics, SBOM generation/consumption, transitive-vulnerability tracing, license posture, ecosystem coverage
beyond npm/pip, and registry/typosquat hygiene — each ≥250 LOC with ≥2 references, narrow `allowed-tools`,
pain-anchored openings, audit-harness installed, wired to the shared MCP (`cve_lookup`, `cve_search`; v0.2.0+
`osv_lookup`). **Known overlap to reconcile:** penetration-tester v3.0.0 already ships
`auditing-npm-dependencies`, `auditing-python-dependencies`, `checking-license-compliance`, and
`tracing-transitive-vulnerabilities`; the Phase 1B bead must differentiate (depth + SBOM/supply-chain identity)
or explicitly re-home those four. Open item — see §6.

**`authentication-validator` — promotion outline.** Stays its own plugin at
`plugins/security/authentication-validator`. Expand the single `validating-authentication-implementations`
skill (1,546 LOC base: `jwt_analyzer.py`, `authentication_check.py`, `password_policy_check.py`) into
gerund-named skills across authN *mechanics*: JWT validation/signature/claims, OAuth2/OIDC flow review, SAML
assertions, password policy + storage (hashing/peppering), MFA enrollment flows, and token-lifecycle checks —
same 13-point scaffolding and MCP wiring as above. Boundary with the umbrella: authentication-validator owns
protocol mechanics; `secpro-access-review` owns access governance and `secpro-session-hardening` owns the
browser session layer.

## 4. Directory layout

Per current marketplace conventions (penetration-tester v3 precedent) and 687's locked MCP layout:

```text
plugins/packages/security-pro-pack/
├── .claude-plugin/plugin.json      # v2.0.0; mcpServers block → ./mcp/dist/index.js
├── README.md
├── 000-docs/                       # pack-level catalog: research 001–010, pain catalog 011,
│                                   # this doc 012, migration table (Phase 2.1, next free number)
├── skills/
│   ├── secpro-framework-gap-audit/
│   │   ├── SKILL.md                # 8-field marketplace frontmatter (685 constraint 1)
│   │   ├── references/             # ≥2 files per skill (13-point bar)
│   │   └── scripts/                # where the job warrants deterministic tooling
│   └── ... (11 more, same shape)
└── mcp/                            # shared MCP server exactly per 687 (src/, data/, dist/index.js)
```

The v1 pack's nested `plugins/01-core-security … 04-infrastructure-security` tree does not carry into v2; its
`performing-security-audits` skill is absorbed by `secpro-owasp-alignment` (row 12). The 3 HEAVY plugins remain
at their existing `plugins/security/<name>/` paths and declare the same shared server in their `plugin.json`
`mcpServers` block (687: one server, many wires).

## 5. Sequencing

1. **Taxonomy locked** — this document (unblocks everything below).
2. **Pain catalog fill** to ≥50 entries against these 12 skill names (existing bead `claude-k7x6`; 011 rule:
   every entry maps to ≥1 skill by the v2.0.0 cut).
3. **Research docs** 001–010 written to final depth (existing Phase 3 beads); each skill's references/ cites
   them.
4. **Skill builds** — 12 umbrella skills + the 2 remaining heavy-hitter promotions (1B/1C), buildable in
   parallel once 1–3 exist.
5. **Shared MCP server** (bead `claude-md8s`) — buildable in parallel with 4; skills land MCP-wired or gain
   the wire in a follow-up pass, per the databricks "MCP first where possible" sequencing.
6. **v2.0.0 cut** (bead `claude-f9mt`) — single release; CHANGELOG carries the full v1→v2 mapping.
7. **Deprecation lane re-anchor** — 686's mechanics apply unchanged, but its dates were keyed to a v2.0.0 cut
   of 2026-05-29 that never happened. **All 686 dates re-anchor at the actual v2.0.0 cut**: sunset = cut
   date plus 90 days (not 2026-08-27), and the v1.x.PATCH banner/tombstone text is templated on the real dates.

## 6. Open items (honest)

- **Pen-tester ↔ dependency-checker overlap** (§3): four dependency-audit skills already live in
  penetration-tester v3.0.0. Resolution owned by the Phase 1B promotion bead; options are differentiation-by-
  depth or re-homing. Not blocking the umbrella taxonomy.
- **Phase 2.1 dispositions** (`claude-43pk`): the 4 SUBSTANTIAL plugins' final placement and the
  `severity1-marketplace` prompt-improver no-successor call.
- **Pain-catalog grounding is prospective**: 011 has schema + distribution but zero filled entries; per-skill
  pain anchors harden when `claude-k7x6` fills the catalog. If the filled catalog materially contradicts a
  cluster boundary, amend this doc by follow-up (additive), not by silent renames.
- **Per-skill MCP tool selection is indicative, not contractual** (687 explicitly leaves final selection to
  skill authors at build time).
- **Skill count may flex ±2 within the 8–14 band** during builds (e.g., splitting `secpro-data-protection` if
  secrets-lifecycle depth demands it) — any rename/split updates the Phase 2.1 migration table in the same PR.

## Status

**LOCKED 2026-07-02** (Backlog Zero Wave 1). Namespace (`secpro-*`, flat) and the 23→12 absorption map are the
contract for the migration table, the pain-catalog skill mappings, and the v2.0.0 skill builds. Re-opening the
namespace or dropping/merging a skill's absorption target requires a follow-up AT-ADEC; the §6 flex items do
not.
