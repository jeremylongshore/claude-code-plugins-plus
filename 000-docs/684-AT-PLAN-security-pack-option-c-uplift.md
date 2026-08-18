<!-- doc-class: record -->

# Security Pack Option C Uplift — Execution Plan

**Status:** DRAFT (awaiting Jeremy's phase-start approval)
**Date:** 2026-05-29
**Author:** jeremy made me do it / -claude
**Audit input:** `/tmp/security-pack-audit-2026-05-29.md` (2026-05-29)
**Decision:** Option C — data-suggested hybrid
**Investigation bead:** `claude-uqen` (closed)

---

## Decision recap

Audit of 30 SKILL.md files showed:

- All A-grade on validator (94–100); validator-illusion confirmed
- 3 HEAVY plugins already have the script substance (penetration-tester 3,138 LOC, dependency-checker 1,570, authentication-validator 1,546)
- 4 SUBSTANTIAL plugins (200–999 LOC)
- 12 LIGHT plugins (template-generated, 100–199 LOC)
- 11 PROMPT-ONLY plugins (0 LOC)
- 0/30 have `000-docs/` research catalog, AT-ADEC records, shared MCP server, or pain catalog

**Option C — chosen:** promote the 3 HEAVY plugins individually to heavy-hitter standard (substance already there, just add the scaffolding) AND rebuild `security-pro-pack` as the umbrella that bundles + deprecates the 23 LIGHT/PROMPT-ONLY plugins. Matches LangChain pattern: heavy individuals + heavy umbrella.

---

## Target end-state (heavy-hitter 13-point bar, applied)

Per LangChain / Databricks reference:

**Per HEAVY plugin (penetration-tester, dependency-checker, authentication-validator):**
- ≥10 docs in own `000-docs/` (or shared catalog with namespace)
- ≥25 skills, each ≥250 LOC
- Multi-reference depth (avg ≥2 reference files per skill)
- Pain-anchored skill openings
- Narrow allowed-tools per skill
- Shared MCP server (umbrella-level)

**At umbrella level (`security-pro-pack` v2):**
- Pain catalog ≥50 entries from primary sources (CVE, OWASP, NIST, Reddit r/netsec, GitHub issues)
- ≥10 research docs in `000-docs/` (auditor patterns, OWASP top-10 crosswalk, NIST/ISO mapping, threat-model methodology, CVE landscape, etc.)
- ≥1 AT-ADEC per major structural choice (umbrella scope, deprecation lane, MCP server boundary)
- CTO-synthesis / pressure-test artifact
- Shared MCP server
- v1.x deprecation release → grace period → v2.0.0 cut

---

## Phased execution

### Phase 0 — Foundation (decision artifacts + scaffold) ~10–15 hrs

Blocking work that has to land before any of Phase 1/2 can start. No skill-level changes.

1. **AT-ADEC: Option C scope choice** — `000-docs/685-AT-ADEC-security-pack-option-c-scope.md`. Records Why Option C over A/B, what's in/out, what deprecation looks like.
2. **AT-ADEC: deprecation lane policy** — what `v1.x deprecate` looks like for 23 plugins (changelog entry, README banner, sunset date, migration pointer).
3. **AT-ADEC: shared MCP server boundary** — is the MCP umbrella-only? Does penetration-tester get its own? (Recommendation: umbrella-only to avoid 4 servers; revisit per heavy-hitter.)
4. **Pack-level `000-docs/` skeleton** under `plugins/packages/security-pro-pack/000-docs/` — 10 stub files following Doc Filing Standard v4.3, each with the heading + table-of-contents.
5. **Pain catalog scaffolding** — `plugins/packages/security-pro-pack/000-docs/00X-DR-PAIN-catalog-master.md` with source-list (GitHub issue queries, OWASP top-10, CVE feed search, NIST SP 800-53 control crosswalks, Reddit r/netsec / r/AskNetsec scrape). Schema for each entry: source URL · date · symptom · root cause · primary affected control.
6. **v2.0.0 branch strategy decision** — single `security-pro-pack@2.0.0` cut vs incremental minor bumps. (Recommendation: single cut after Phase 2 so v1→v2 communicates clearly.)

**Deliverable:** 3 AT-ADEC docs + 10 stub research docs + pain catalog header. No skill edits.

### Phase 1 — Heavy-hitter promotions (3 plugins, parallel-able) ~50–70 hrs each

For each of: `penetration-tester`, `dependency-checker`, `authentication-validator`.

Per-plugin checklist:

1. **Expand single skill → 25 skills.** Current scripts cover broad capability; split them into narrow skills (e.g., `penetration-tester` 1-skill → 25: `discover-attack-surface`, `enumerate-services`, `analyze-tls-config`, `audit-jwt-implementation`, etc.). Each skill ≥250 LOC.
2. **Pain-anchor every skill opening.** "Use when: SOC2 auditor found 12 of your CRITICAL findings come from missing JWT signature validation at the edge proxy — threshold ≥1 unsigned token in 24h sampling."
3. **Add `references/` ≥2 files per skill.** Reuse research docs + reference threat models / CVE entries.
4. **Narrow `allowed-tools` per skill** — no blanket `Bash`, only `Bash(curl:*)`, `Bash(openssl:*)`, etc.
5. **Per-plugin `000-docs/` if pack-level isn't enough.** Likely lives in umbrella but namespace per plugin (e.g., `pen-test/`, `dep-check/`, `auth-validator/` subdirs in shared catalog).
6. **Plugin-level AT-ADEC** for structural decisions specific to that plugin (e.g., dep-checker: SBOM format choice).
7. **Wire to umbrella MCP** once Phase 2.3 lands.

**Sequencing:** these are independent and can be Phase 1A / 1B / 1C in parallel if multiple sessions, OR serial. Recommend serial (penetration-tester first — biggest LOC base, biggest payoff for "best in class" claim).

### Phase 2 — Umbrella rebuild (`security-pro-pack` v2) ~80–120 hrs

1. **Inventory + classify 23 LIGHT/PROMPT-ONLY plugins.** Per plugin: keep-as-command, fold-into-skill, deprecate-clean.
2. **Design v2 namespace.** Skills under `security-pro-pack/skills/<domain>/<skill>` (compliance/, crypto/, infra/, web/, identity/).
3. **Shared MCP server.** TypeScript or Python (decision in Phase 0.3). Exposes: CVE lookup, OWASP top-10 retrieval, SOC2 control crosswalk, NIST control retrieval, common scanner harness. Lives at `plugins/packages/security-pro-pack/mcp/`.
4. **Pain catalog ≥50 entries.** Filled from sources defined in Phase 0.5.
5. **CTO-synthesis artifact** — a council pressure-test decision record (local governance archive). Convene the executive decision council if non-trivial trade-offs surface (e.g., MCP server licensing — MIT or proprietary).
6. **v1.x deprecation release.** PR per plugin or batch PR: README banner, plugin.json `deprecated: true`, sunset date 90d out. CHANGELOG entry.
7. **v2.0.0 cut.** Single release; CHANGELOG documents v1 plugin → v2 skill mapping for downstream users.

### Phase 3 — Research depth (parallel with 1 + 2) ~30–50 hrs

1. **≥10 research docs** in pack `000-docs/`:
   - Auditor patterns extracted from Big 4 audit methodology (Deloitte/PwC/EY/KPMG SOC2 playbooks — public references only)
   - OWASP Top 10 (2024 edition) crosswalk to pack skills
   - NIST SP 800-53 / ISO 27001 control crosswalk
   - CVE landscape — what categories dominate, which scanners catch what
   - Threat-modeling methodology (STRIDE / PASTA / LINDDUN)
   - Zero-trust architecture reference
   - PCI DSS v4.0 mapping
   - HIPAA Security Rule mapping
   - GDPR Article 32 technical measures mapping
   - SOC2 Trust Services Criteria mapping
2. **Anthropic skill-architecture patterns research doc.** Same as Databricks pack — extract patterns from first-party Anthropic skills, reference how heavy-hitter packs use them.

---

## Estimated total: 270–365 hours

- Phase 0: 10–15 hrs
- Phase 1: 150–210 hrs (3 × 50–70)
- Phase 2: 80–120 hrs
- Phase 3: 30–50 hrs (parallel-able with Phase 1+2)

Higher than the plan's "200–250 hr" because Option C is broader than Option A (single flagship) AND the audit revealed less script substance in the LIGHT tier than Option A's hours assumed. Lower than Option B because we leverage the umbrella to avoid 4 independent rebuilds.

---

## Sequencing recommendation

**Quarter-scale commit needed.** This is not a "weekend project." Realistic sequencing:

- **Week 1:** Phase 0 (foundation). Lands all AT-ADEC + scaffolding. Decision points all unblocked.
- **Weeks 2–6:** Phase 1A — `penetration-tester` heavy-hitter promotion. First flagship.
- **Weeks 7–10:** Phase 1B + 1C in parallel — `dependency-checker` + `authentication-validator`. Phase 3 research running in background.
- **Weeks 11–14:** Phase 2 — umbrella rebuild, deprecation lane, v2.0.0 cut.

Or, if cohort capacity exists: subcontractor pairs take Phase 1A/1B/1C in parallel weeks 2–6; Jeremy owns Phase 0 + Phase 2 directly.

---

## Risks

1. **Validator passes but substance fails again.** The bar is the heavy-hitter 13-point checklist, NOT the validator score. Every PR must self-attest "X of 13 points met" or get a counterpart in the audit table.
2. **Cohort skill mismatch.** Heavy-hitter authoring requires security domain knowledge — JWT internals, OWASP categories, threat-model methodologies. Subcontractor pairing for Phase 1 may need a domain-knowledgeable reviewer.
3. **MCP server scope creep.** "One MCP server for the whole pack" can balloon. Phase 0.3 AT-ADEC must define narrow scope: CVE lookup + OWASP retrieval + control crosswalk lookup. Leave scanning/execution to the skills.
4. **Deprecation breakage.** 23 plugins have 45,000+ downloads cumulative (per package READMEs); users have installs depending on the v1 plugin names. v1.x deprecation lane MUST include migration table mapping every v1 command → v2 skill.
5. **Federico's UX cut is a real-user complaint.** The `${CLAUDE_SKILL_DIR}` path issue is small but the cohort will hit it again. Suggested side bead before Phase 0 starts so it lands in v1.x deprecation release.

---

## Beads to file when Jeremy gives the green light

Epic: `Promote security plugin pack to heavy-hitter standard (Option C)`

Phase 0 sub-beads:
- `AT-ADEC: scope (Option C choice) for security pack v2`
- `AT-ADEC: deprecation lane policy for v1 security plugins`
- `AT-ADEC: shared MCP server boundary for security-pro-pack v2`
- `Stub 10 research docs under security-pro-pack 000-docs/`
- `Pain catalog scaffolding + source list under security-pro-pack`

Phase 1 sub-beads (3, one per heavy-hitter):
- `Promote penetration-tester to heavy-hitter (25 skills, references, MCP wire)`
- `Promote dependency-checker to heavy-hitter`
- `Promote authentication-validator to heavy-hitter`

Phase 2 sub-beads:
- `Inventory + classify 23 LIGHT/PROMPT-ONLY plugins for v2 disposition`
- `Design security-pro-pack v2 namespace + skill taxonomy`
- `Build shared MCP server for security-pro-pack v2`
- `Fill pain catalog to 50 entries from primary sources`
- `Cut v1.x deprecation release across 23 plugins`
- `Cut security-pro-pack v2.0.0 release`

Phase 3 sub-beads:
- `Author 10 research docs in security-pro-pack 000-docs/`
- `Author Anthropic skill-architecture patterns research doc`

Plus side beads (NOT bundled, file alongside):
- `Federico ${CLAUDE_SKILL_DIR} path-resolution UX cut (1-liner fix)`
- `Re-populate freshie inventory DB (post-2026-05-12 drift)`

---

## What I need from Jeremy before starting

1. **Approval to file the epic + 14 sub-beads above** (so the work is bd-tracked).
2. **Phase 0 vs Phase 0 + Federico-fix start order** — does the UX cut block-ship first, or roll into Phase 2.6 deprecation release?
3. **Cohort participation y/n** — does Phase 1 get parallel subcontractor pairs, or is this serial single-author?
4. **Heavy-hitter PR cadence** — one big PR per phase (LangChain pattern) or many small PRs (cleaner review, slower momentum)?

If you want me to just start Phase 0 now, say "go" — I'll file the bead epic + open Phase 0 work.

---

## Cross-references

- Audit: `/tmp/security-pack-audit-2026-05-29.md`
- Heavy-hitter standard source: `plugins/saas-packs/langchain-py-pack/` + `plugins/saas-packs/databricks-pack/`
- Federico LinkedIn DM (2026-05-28) — surfaced `${CLAUDE_SKILL_DIR}` UX cut + structural concerns
- Investigation bead: `claude-uqen` (closed 2026-05-29)
