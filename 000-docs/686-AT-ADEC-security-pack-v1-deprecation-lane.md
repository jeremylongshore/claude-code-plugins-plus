<!-- doc-class: record -->

---
filing_code: AT-ADEC-SECURITY-PACK-V1-DEPRECATION-LANE-2026-05-29
date: 2026-05-29
acting_head_of_board: Jeremy Longshore
status: locked
scope: 23 LIGHT/PROMPT-ONLY plugins absorbed into security-pro-pack v2.0.0
inputs:
  - 000-docs/684-AT-PLAN-security-pack-option-c-uplift.md
  - 000-docs/685-AT-ADEC-security-pack-option-c-scope.md
  - /tmp/security-pack-audit-2026-05-29.md (audit table)
  - Reference: marketplace catalog and pnpm/npm install metrics (~45,000+ cumulative downloads across security plugins per package READMEs)
affects: 23 plugin marketplace listings, downstream user installs, plugin.json deprecated flag, marketplace.json catalog, README banners, CHANGELOG entries
---

# Security Pack v1.x Deprecation Lane Policy

## Mission

23 plugins (12 LIGHT, 11 PROMPT-ONLY per the 2026-05-29 audit) will be absorbed into `security-pro-pack` v2.0.0. They have cumulative downstream installs (~45K combined per marketplace metadata). Yanking them in a single release would break user installs and damage marketplace trust. This decision record locks the deprecation mechanics: how each absorbed plugin announces its sunset, what users see, what they migrate to, and on what timeline.

## The 23 absorbed plugins

### LIGHT tier (12)
`access-control-auditor`, `encryption-tool`, `pci-dss-validator`, `compliance-report-generator`, `soc2-audit-helper`, `gdpr-compliance-scanner`, `owasp-compliance-checker`, `vulnerability-scanner` (security/), `compliance-checker` (devops/), `csrf-protection-validator`, `security-incident-responder`, plus the legacy `security-pro-pack` v1 itself (102 LOC).

### PROMPT-ONLY tier (11)
`severity1-marketplace`, `hipaa-compliance-checker`, `secret-scanner`, `ssl-certificate-manager`, `xss-vulnerability-scanner`, `data-privacy-scanner`, `security-misconfiguration-finder`, `sql-injection-detector`, `api-security-scanner` (api-development/), `security-audit-reporter`, `session-security-checker`.

## Deprecation lane mechanics — per-plugin

Every plugin in the absorption list ships **one v1.x.PATCH release** containing:

### 1. `plugin.json` flag

```json
{
  "name": "<plugin-name>",
  "version": "1.X.PATCH",
  "deprecated": true,
  "deprecation_message": "This plugin is superseded by security-pro-pack v2.0.0. Install: claude plugin install security-pro-pack. Sunset: 2026-08-27 (90 days from v2.0.0 cut). Migration table: <link to v1-to-v2-migration.md>"
}
```

### 2. README banner — top of file, above the title

```markdown
> [!WARNING]
> **Deprecated — sunsets 2026-08-27 (90 days from security-pro-pack v2.0.0 cut on 2026-05-29).**
> This plugin has been superseded by `security-pro-pack` v2.0.0 which bundles its capabilities with shared infrastructure (MCP server, pain catalog, research docs).
> **Migration:** `claude plugin install security-pro-pack` then use `<v2-skill-path>` instead of this plugin's commands. See v1-to-v2-migration.md for the full mapping.
```

### 3. CHANGELOG.md entry per plugin

```markdown
## [1.X.PATCH] — 2026-05-29

### Deprecated
- This plugin is superseded by `security-pro-pack` v2.0.0.
- **Sunset date:** 2026-08-27 (90 days).
- Migration: see security-pro-pack/000-docs/00N-DR-MGRD-v1-to-v2-migration.md.
- No new features will be added; only critical security patches until sunset.
```

### 4. Marketplace catalog entry — `marketplace.extended.json`

```json
{
  "name": "<plugin-name>",
  "deprecated": true,
  "successor": "security-pro-pack",
  "sunset_date": "2026-08-27"
}
```

The marketplace build pipeline (`scripts/build.mjs`) must surface `deprecated: true` plugins with a visual treatment on the catalog page (struck-through name, "Deprecated" badge, link to successor). This is a small marketplace-frontend change tracked under the umbrella v2.0.0 cut (Phase 2.6 bead `claude-f9mt`).

## Grace period: 90 days

**Why 90 days, not 30 or 180:**

- 30 days is too aggressive — quarterly-release shops won't see the deprecation in time.
- 180 days is too long — keeps deprecated infrastructure live well after the absorption rationale fades from memory.
- 90 days matches Anthropic's own deprecation cadence for model versions and gives downstream users one full quarter to migrate.

## Sunset behavior

On sunset date (2026-08-27 if security-pro-pack v2.0.0 ships 2026-05-29):

1. **Plugin source is removed** from `plugins/security/<name>/`. The marketplace listing is removed.
2. **Existing user installs continue to function** — they remain pinned to v1.X.PATCH on disk. The CLI does not break their installs.
3. **`claude plugin install <deprecated-name>` returns an error** with the successor pointer message.
4. **A final "tombstone" release** v1.X.PATCH+1 ships on sunset date with README that says only: "This plugin is sunset as of 2026-08-27. Install `security-pro-pack` instead."

## Migration table — required artifact

A single migration table at `plugins/packages/security-pro-pack/000-docs/00N-DR-MGRD-v1-to-v2-migration.md` maps every absorbed v1 plugin → its v2 skill or command path. Schema per row:

| v1 plugin | v1 command/skill | v2 skill path | Notes |
|---|---|---|---|
| `soc2-audit-helper` | `assist-with-soc2-audit-preparation` | `security-pro-pack/skills/compliance/soc2-audit-preparation` | Forge-template upgraded to research-anchored skill |
| `secret-scanner` | `scan-for-secrets` | `security-pro-pack/skills/web/secret-scanning` | Prompt-only → wired to MCP CVE lookup |
| ... | ... | ... | ... |

Building this table is part of Phase 2.1 (bead `claude-43pk` — inventory + classify).

## What does NOT change in deprecated plugins

- **Existing scripts continue to work** during the grace period. No removal of working code.
- **Test suites continue to run** in CI. No suppression of validator warnings.
- **No silent breakage** — every v1.X.PATCH release must validate clean at marketplace tier.

## Edge cases

### Plugin has a non-obvious migration path

E.g., `severity1-marketplace` is named for the "severity 1" use case but its prompt-improver skill is more general. Phase 2.1 decides: keep its capability in v2 under a new skill name, OR mark it as no-direct-replacement (rare; migration table notes "no direct successor — see X for partial overlap").

### User has a CI workflow pinned to a v1 plugin

Existing CI keeps working until they upgrade. The deprecation message in `plugin.json` is the upgrade signal; we don't need a pre-emptive CI integration.

### A plugin is more popular than expected

If download metrics show a plugin has 10x the install base of its peers, Phase 2.1 inventory may upgrade it to "promote to heavy-hitter" status (joining the 3 chosen in Phase 1) and drop it from this deprecation list. That's a Phase 2.1 escalation, not a deprecation-lane policy change.

## Constraints carried forward

1. **No `--no-verify` skip-CI commits during deprecation work.** Every v1.X.PATCH release passes validator, lint, and the marketplace build.
2. **Federico's `${CLAUDE_SKILL_DIR}` UX cut** (side bead `claude-atyq`) is fixed in the same v1.X.PATCH release for affected plugins (at minimum `soc2-audit-helper` per Federico's report).
3. **Migration table commit must precede the v1.X.PATCH releases.** Users hitting the README banner need a destination link that works.

## Status

**LOCKED 2026-05-29.** Sunset date 2026-08-27 is conditional on security-pro-pack v2.0.0 cutting 2026-05-29 — slips with the v2.0.0 cut. Re-opening requires a new AT-ADEC.
