<!-- doc-class: record -->

---

filing_code: AT-ADEC-SECURITY-PACK-OPTION-C-SCOPE-2026-05-29
date: 2026-05-29
acting_head_of_board: Jeremy Longshore
status: locked
scope: plugins/security/\* + plugins/devops/compliance-checker + plugins/database/database-audit-logger + plugins/api-development/api-security-scanner + plugins/packages/security-pro-pack
inputs:

- /tmp/security-pack-audit-2026-05-29.md (investigation table, 30 SKILL.md files scored on validator + freshie + 13-point heavy-hitter rubric)
- 000-docs/684-AT-PLAN-security-pack-option-c-uplift.md (phased execution plan)
- Investigation bead claude-uqen (closed 2026-05-29)
- Reference heavy-hitter standard: plugins/saas-packs/langchain-py-pack/ (33 skills, 11,249 LOC), plugins/saas-packs/databricks-pack/ (24 skills, 6,669 LOC)
- Federico Sapuppo LinkedIn DM (2026-05-28) — surfaced UX cut on soc2-audit-helper and validator-illusion structural concern
  affects: 3 HEAVY plugins (penetration-tester, dependency-checker, authentication-validator), 4 SUBSTANTIAL plugins, 23 LIGHT/PROMPT-ONLY plugins, security-pro-pack umbrella, marketplace listings, ~45,000+ cumulative downstream installs

---

# Security Plugin Pack — Option C Scope Decision

## Mission

The security plugin pack has been growing thin while LangChain and Databricks packs set a heavy-hitter bar Jeremy wants the security work to meet. The 2026-05-29 audit of 30 SKILL.md files surfaced three options for response. This decision record locks **Option C — data-suggested hybrid** as the chosen scope and records the alternatives steel-manned, so future readers (and downstream cohort contributors) understand the rejected paths.

## The three options that were on the table

### Option A — Pragmatic single-flagship

Rewrite `security-pro-pack` as the unified heavy-hitter. Deprecate all other security plugins into it. Estimated 60–90 hours.

**Steel-man:** simplest scope. One pack, one PR cadence, one MCP server, one CHANGELOG. Cohort can focus all attention on one artifact. Lowest coordination cost.

**Why rejected:** the audit revealed three plugins ALREADY have heavy-hitter script substance (`penetration-tester` 3,138 LOC, `dependency-checker` 1,570 LOC, `authentication-validator` 1,546 LOC). Folding them into the umbrella would either (a) bury their existing identity in a generic namespace, harming discoverability for users who currently install them directly, or (b) keep them as separate plugins inside the umbrella, which collapses to Option C anyway.

### Option B — Full multi-pack heavy-hitter uplift (4 independent rebuilds)

Uplift `security-pro-pack` + `soc2-audit-helper` + `penetration-tester` + `api-security-scanner` separately as four independent heavy-hitter packs. Estimated 200–250 hours.

**Steel-man:** matches the "every domain gets its own flagship" pattern. Each pack has its own pain catalog tuned to its domain, its own MCP server, its own deprecation lane. Maximum surface area for marketing claims.

**Why rejected:** the audit revealed `api-security-scanner` has **zero** real script LOC (the original audit's "74 LOC TS placeholder" claim was not reproduced — only 2 sh template helpers exist). `soc2-audit-helper` has 129 LOC of forge-template Python. Each of those is closer to a green-field rebuild than an uplift. The 200–250 hr estimate is conservative for 4 green-field-ish packs; realistically ~350 hr. And four parallel pain catalogs / four MCP servers fragments the shared infrastructure that makes heavy-hitter packs efficient.

### Option C — Data-suggested hybrid (CHOSEN)

Promote the 3 HEAVY plugins (`penetration-tester`, `dependency-checker`, `authentication-validator`) individually to heavy-hitter standard — substance is already there, just add scaffolding. Rebuild `security-pro-pack` as the umbrella that bundles + deprecates the 23 LIGHT/PROMPT-ONLY plugins. Estimated 270–365 hours.

**Why chosen:**

1. **Leverages existing substance.** The 3 HEAVY plugins already have 6,254 LOC of working Python. Heavy-hitter promotion is _scaffolding + skill expansion_, not a rewrite.
2. **One shared MCP server, one shared research catalog.** The 3 HEAVY plugins and the umbrella all wire to a single MCP at `plugins/packages/security-pro-pack/mcp/`. Pain catalog lives once at the umbrella level and is referenced by all four.
3. **Discoverability preserved.** Users who currently install `penetration-tester` keep installing `penetration-tester`. The umbrella adds a single-package install path for users who want the whole stack.
4. **Matches LangChain pattern.** LangChain's 33-skill pack is itself a heavy-hitter, AND specific high-value skills inside it (LCEL, agents, retrievers) are individually identifiable. Same here: penetration-tester is the LCEL of this pack.
5. **Deprecation lane is cleaner.** 23 plugins go away into a single umbrella v2.0.0 rather than into 4 distinct packs (which would force every deprecated plugin to pick a destination pack).

## Scope — what's IN

### Plugins promoted to individual heavy-hitter

1. **`plugins/security/penetration-tester`** (3,138 LOC base → 25 skills × ≥250 LOC each)
2. **`plugins/security/dependency-checker`** (1,570 LOC base → 25 skills × ≥250 LOC each)
3. **`plugins/security/authentication-validator`** (1,546 LOC base → 25 skills × ≥250 LOC each)

### Umbrella — security-pro-pack v2

1. Bundle + deprecate the 23 LIGHT/PROMPT-ONLY plugins. v2.0.0 is the new umbrella.
2. Shared MCP server at `plugins/packages/security-pro-pack/mcp/` (CVE lookup + OWASP retrieval + control crosswalk).
3. Pain catalog ≥50 entries at `plugins/packages/security-pro-pack/000-docs/`.
4. Research catalog ≥10 docs at `plugins/packages/security-pro-pack/000-docs/`.
5. v1.x deprecation release on the 23 absorbed plugins (90-day sunset, migration table).

### 4 SUBSTANTIAL plugins — case-by-case in Phase 2.1

`cors-policy-validator` (815 LOC), `database-audit-logger` (434 LOC), `security-headers-analyzer` (262 LOC), `input-validation-scanner` (204 LOC). The Phase 2.1 inventory bead (`claude-43pk`) decides per-plugin: promote to heavy-hitter, fold into umbrella, or keep as separate plugin under the umbrella. Default disposition: keep as separate plugin under the umbrella with reference depth added — they're already mid-tier and have a sub-domain identity worth preserving.

## Scope — what's OUT

- **Crypto pack** (`plugins/crypto/`). Confirmed by Jeremy as example reference only. `wallet-security-auditor` (in crypto/, not security/) is the only heavy-hitter in crypto today. Crypto pack uplift is a separate decision and plan.
- **Blocknative June 19 emergency** — handled separately via bead `claude-xe9g` (gas-fee-optimizer migration).
- **Top-level non-plugin `skills/*-security-*` paths** (e.g., `skills/04-security-advanced/soc2-compliance-checker`). These are legacy positioning; not in the marketplace plugin namespace. Out of scope for this work.
- **LangChain pack** — used as reference standard, not modified.

## Constraints carried forward

1. **8-field marketplace frontmatter** on every skill (ALWAYS_REQUIRED — schema 3.7.0 NON-NEGOTIABLES).
2. **Heavy-hitter 13-point checklist** is the bar, not validator score. Every PR must self-attest "X of 13 points met" or be paired with an audit entry showing the gap is deliberate.
3. **Enforcement travels with the code.** Every new heavy-hitter installs `@intentsolutions/audit-harness` and runs the 7-layer testing taxonomy per the Intent Solutions Testing SOP.
4. **Doc Filing Standard v4.3** applies to all `000-docs/` content.
5. **No silent regressions in v1 deprecated plugins** before sunset. CHANGELOG and README banner must announce sunset; downstream installs continue to work for the 90-day grace period.

## Open decisions left to subsequent AT-ADECs

- **MCP server scope + language choice** — locked in `686-AT-ADEC` (boundary) and the Phase 2.3 implementation bead.
- **Deprecation lane mechanical details** — locked in `687-AT-ADEC` (lane policy).
- **4 SUBSTANTIAL disposition** — Phase 2.1 inventory bead `claude-43pk` produces a per-plugin matrix.
- **Cohort participation y/n** — execution-time decision; not architectural.

## Status

**LOCKED 2026-05-29.** Re-opening this decision requires a new AT-ADEC superseding this one with the data + reasoning for the new direction.
