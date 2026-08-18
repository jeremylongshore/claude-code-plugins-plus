<!-- doc-class: record -->

---

filing_code: AT-ADEC-CLAUDE-CODE-PLATFORM-CHANGELOG-IMPACT-2026-05-27
date: 2026-05-27
acting_head_of_board: Claude (designated by Jeremy Longshore 2026-05-27)
status: locked
scope: repo-wide (claude-code-plugins / Tons of Skills marketplace)
inputs:

- Claude Code changelog 0.2.21 through 2.1.153 (https://code.claude.com/docs/en/changelog)
- Current SCHEMA_CHANGELOG.md (schema 3.6.0 as of 2026-05-26)
- scripts/validate-skills-schema.py (v7.0)
- scripts/validate-unicode-hygiene.py
- .claude/skills/validate-mcp/, validate-skillmd/, validate-agent/, validate-plugin/
- .claude/skills/skill-creator/, agent-creator/
  affects: validators, schema versioning, schema changelog, skill-creator templates, agent-creator templates, MCP validators, plugin manifests, hook validators, plugin docs, the existing 400+ plugins in the marketplace, AND downstream consumers like the databricks-pack v2 rebuild

---

# Claude Code Platform Changelog Impact — Repo-Wide Decision Record

## Mission

The Claude Code platform shipped substantial new capabilities between schema 3.6.0 (locked in `SCHEMA_CHANGELOG.md` on 2026-05-26) and the current 2.1.153 release (2026-05-28). This decision record catalogs the platform changes that materially affect ANY part of this repo — the validators that gate marketplace ingestion, the schema version, the skill/agent/plugin scaffolding, the MCP validators, the hook docs, and the 400+ already-published plugins.

The doc is repo-wide. Downstream consumers (the databricks-pack v2 rebuild at `plugins/saas-packs/databricks-pack/000-docs/`, future partner-integration work, etc.) reference THIS file for the platform feature surface they should build against. They do not maintain their own copies of the same mapping.

## The 9 platform changes that need repo-wide response

### Change 1 — Skills + slash commands accept `disallowed-tools` frontmatter

**Source:** Claude Code 2.1.152 (2026-05-27).

> Skills and slash commands can now set `disallowed-tools` in frontmatter to remove tools from the model while the skill is active.

**Validator impact:**

- `scripts/validate-skills-schema.py` must add `disallowed-tools` to the recognized OPTIONAL frontmatter fields for both skills and slash commands. Currently the validator's `ALWAYS_REQUIRED` set is 8 fields (locked per `SCHEMA_CHANGELOG.md` NON-NEGOTIABLES); `disallowed-tools` is OPTIONAL and goes in the "Optional frontmatter (schema 3.5.0+)" section per repo CLAUDE.md.
- Validation rule: must be a non-empty string OR a YAML list of strings, matching the existing `allowed-tools` shape.
- Cross-field rule: same tool name appearing in BOTH `allowed-tools` AND `disallowed-tools` is an ERROR (mirrors the existing 3.5.0 visibility-gating overlap rule).

**Schema impact:** SCHEMA_VERSION bumps to **3.7.0** (the next minor) because this is an additive observable change to validator output.

**Skill-creator impact:** `~/.claude/skills/skill-creator/` interactive flow should offer `disallowed-tools` as an optional field with explanation. Forge mode templates should default-include `disallowed-tools: [Bash(rm:*), Bash(curl:*), Bash(wget:*), Edit(.env), Write(.env)]` as a defense-in-depth example unless the API surface justifies broader bash.

**Agent-creator impact:** Agents already use `disallowedTools` (camelCase, denylist semantics) per the spec. CLAUDE.md note: "Agents use `disallowedTools` (denylist); skills use `allowed-tools` (allowlist)." Now skills ALSO support `disallowed-tools` (kebab-case) — this is a parallel field, not a unification. The validator must reject `disallowedTools` (camelCase) on skills and `disallowed-tools` (kebab-case) on agents.

**Existing-plugins impact:** Audit-find existing plugins that have broad `allowed-tools` (e.g. `Bash`, `Bash:*`, or any plugin that allows-all). Add `disallowed-tools` for high-risk operations as a defense-in-depth pass. Track as a follow-up sweep, not a blocking migration.

### Change 2 — Hook `if:` conditional matcher (permission-rule syntax)

**Source:** Claude Code 2.1.85 (2026-03-26).

> Added conditional `if` field for hooks using permission rule syntax (e.g., `Bash(git *)`) to filter when they run, reducing process spawning overhead.

**Validator impact:**

- `.claude/skills/validate-hook/` needs schema update to recognize the optional `if:` field on every hook handler. Value type: a permission-rule string identical to the `permissions.allow`/`deny` syntax.
- New validation: if `if:` is present, validate the rule string with the same parser used for `permissions.*` validation. Surface bad rules with the same actionable error message style.

**Schema impact:** Hooks schema in `references/anthropic-hooks-reference.md` (the canonical spec snapshot) needs `if:` documented as optional on each handler type. SCHEMA_VERSION bump captured in Change 1.

**Documentation impact:** The hook authoring guide should add an `if:` examples section showing common patterns: `Bash(git push*)`, `Bash(databricks bundle deploy*)`, `Edit(.env*)`, etc. Emphasize the perf win (no shell spawn unless the rule matches).

**Existing-plugins impact:** Plugins with hooks that fire on every Bash invocation and then exit-fast based on internal regex are the audit targets. Convert their hooks to use `if:` declaratively. Notable candidates: any plugin doing pre-commit-style checks, any plugin with audit-log hooks.

### Change 3 — Hook `args: string[]` exec form + `continueOnBlock` for PostToolUse

**Source:** Claude Code 2.1.139 (2026-05-11).

> Added hook `args: string[]` field (exec form) that spawns the command directly without a shell, so path placeholders never need quoting. Added hook `continueOnBlock` config option for `PostToolUse` — set to `true` to feed the hook's rejection reason back to Claude and continue the turn.

**Validator impact:** `.claude/skills/validate-hook/` schema additions:

- `args: string[]` is a valid alternative to `command: string`. Validator must accept either-or, not both.
- `continueOnBlock: boolean` is valid only on `PostToolUse` handlers. Reject on PreToolUse / SessionStart / etc. with a clear error.

**Schema impact:** Both fields go in the hook-handler spec snapshot at `references/anthropic-hooks-reference.md`.

**Documentation impact:** Update the hook authoring guide to explain WHY exec-form is preferred (no shell-quoting bugs with paths containing spaces, special chars, etc.) and when `continueOnBlock: true` is appropriate (auto-retry patterns where Claude needs to see the rejection reason to explain the recovery to the user).

**Existing-plugins impact:** Plugins with hooks that use shell command strings with embedded `${path}` placeholders are the audit targets. Migration to `args:[]` form eliminates quoting fragility. Track as opportunistic, not urgent.

### Change 4 — `defer` permission decision in PreToolUse hooks

**Source:** Claude Code 2.1.89 (2026-04-01).

> Added `"defer"` permission decision to `PreToolUse` hooks — headless sessions can pause at a tool call and resume with `-p --resume` to have the hook re-evaluate.

**Validator impact:** `.claude/skills/validate-hook/`: the documented set of valid `permissionDecision` values must add `"defer"` alongside `"allow"`, `"deny"`, `"ask"`. Currently the validator may treat `"defer"` as unknown.

**Schema impact:** Captured in the hooks spec snapshot.

**Documentation impact:** Hook authoring guide gains a section explaining the headless/scripted-flow use case: hook stages an operation for later approval, exits cleanly, the script resumes with `-p --resume` after a separate workflow step grants approval. Useful pattern for CI/CD where AI staged a destructive operation but human approval is required.

**Existing-plugins impact:** None — purely additive capability. Not a migration target.

### Change 5 — MCP tool result `_meta["anthropic/maxResultSizeChars"]` annotation

**Source:** Claude Code 2.1.91 (2026-04-02).

> Added MCP tool result persistence override via `_meta["anthropic/maxResultSizeChars"]` annotation (up to 500K), allowing larger results like DB schemas to pass through without truncation.

**Validator impact:** `.claude/skills/validate-mcp/`: the spec snapshot for MCP tool result format must document `_meta` as a valid optional field. The annotation key `anthropic/maxResultSizeChars` is reserved and must be a number 0 ≤ N ≤ 500000.

**Schema impact:** Captured in the MCP spec snapshot at `references/anthropic-mcp-spec-snapshot.md` (or wherever the canonical MCP spec lives in this repo).

**Documentation impact:** MCP server authoring guide should document the annotation as the canonical way to bypass the default token cap on large tool responses (e.g., 30-day system table pulls, schema introspections). Provide example code.

**Existing-plugins impact:** Plugins with MCP servers that return large datasets (database schemas, audit-log dumps, billing rows, lineage graphs) are the audit targets. Adding the annotation prevents truncation. Most MCP plugins won't need this — only the data-heavy ones.

### Change 6 — `SessionStart` hook can set session title + `reloadSkills`

**Source:** Claude Code 2.1.152 (2026-05-27).

> `SessionStart` hooks can now set the session title via `hookSpecificOutput.sessionTitle` on startup and resume. `SessionStart` hooks can now return `reloadSkills: true` to re-scan skill directories, making skills installed by the hook available in the same session.

**Validator impact:** `.claude/skills/validate-hook/`: the `hookSpecificOutput` shape for `SessionStart` handlers must include the optional `sessionTitle: string` and `reloadSkills: boolean` fields.

**Schema impact:** Captured in hooks spec snapshot.

**Documentation impact:** Hook authoring guide gains a section on session-title hooks — most useful for plugins that install context-specific skills based on the user's working directory or environment (auto-detecting Databricks workspace, AWS account, etc.).

**New slash command:** `/reload-skills` (also in 2.1.152) — this is a Claude Code built-in, not something we ship, but the slash-command suggestion lists and docs across the repo may need to mention it as a way for users to refresh skills without restarting.

**Existing-plugins impact:** Plugins that ship setup walkthroughs (e.g., partner-portal, repo-blueprint, etc.) benefit from this — users completing the walkthrough get the new skills immediately without restart.

### Change 7 — `MessageDisplay` hook event

**Source:** Claude Code 2.1.152 (2026-05-27).

> Added a `MessageDisplay` hook event that lets hooks transform or hide assistant message text as it is displayed.

**Validator impact:** `.claude/skills/validate-hook/`: `MessageDisplay` must be added to the recognized hook event allowlist (currently ~30 events per the validate-hook skill's reference).

**Schema impact:** Captured in hooks spec snapshot.

**Documentation impact:** Hook authoring guide should document the new event with a security-relevant example: redacting sensitive patterns (workspace IDs, IAM role ARNs with account numbers, customer email addresses) from assistant output before display. Useful for plugins handling regulated content.

**Existing-plugins impact:** No migration needed — purely additive. Plugins that surface PII or customer-sensitive data in assistant responses (any plugin doing audit-log reads, security review, customer-data introspection) are candidates for adding MessageDisplay hooks as a follow-up pass.

### Change 8 — `pluginSuggestionMarketplaces` managed setting

**Source:** Claude Code 2.1.152 (2026-05-27).

> Added `pluginSuggestionMarketplaces` managed setting: admins can allowlist org marketplaces whose plugins may be suggested via context-aware tips.

**Validator impact:** No direct validator change (this is a Claude Code user-side setting, not a plugin-side declaration). BUT the marketplace.json validator may want to document the field so that enterprise consumers know how to allowlist Tons of Skills if they want to.

**Documentation impact:** The Tons of Skills marketplace docs (and the `validate-marketplace` skill) should mention that enterprise admins can declare this marketplace in `pluginSuggestionMarketplaces` to let context-aware tips suggest plugins from here.

**Existing-plugins impact:** None for plugin authors. Marketplace-level concern.

### Change 9 — Schema 3.6.0 self-declared config pattern is now well-trafficked

**Source:** Built on the existing 3.6.0 `required_environment_variables` + `metadata.intent-solutions.config` fields, surfaced more visibly through 2.1.139's `claude agents` improvements and 2.1.108's `claude doctor` integration.

**Implication:** The `000-docs/264-DR-GUID-skill-config-pattern.md` document is now load-bearing for partnership skills (e.g., the Databricks-MCP integration and other prospective partner listings). Plugins that need user-supplied env vars or config keys should consistently use this pattern, not invent their own.

**Validator impact:** Already in place since 3.6.0. No change needed; just elevated visibility.

**Documentation impact:** The skill-creator interactive flow should prompt for `required_environment_variables` and `metadata.intent-solutions.config` whenever a skill's allowed-tools includes patterns that suggest external system integration (Bash(databricks:_), Bash(aws:_), Bash(gh:\*), MCP server invocations, etc.).

## Concrete script + skill changes needed

| Artifact                                                                                                                 | Change                                                                                                                                                                                                                                                                          | Owner                          | Blocking?                                                                           |
| ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ----------------------------------------------------------------------------------- |
| `scripts/validate-skills-schema.py`                                                                                      | Add `disallowed-tools` as optional skill+command field. Reject `disallowedTools` (camelCase) on skills; keep accepting on agents. Cross-field overlap check with `allowed-tools`. Bump SCHEMA_VERSION to 3.7.0.                                                                 | repo maintainer                | YES — blocks Change 1 across the marketplace                                        |
| `000-docs/SCHEMA_CHANGELOG.md`                                                                                           | New section: "3.7.0 (2026-05-27) — disallowed-tools field on skills + commands; hook if/args/continueOnBlock/defer additions; MCP \_meta annotation; SessionStart sessionTitle + reloadSkills; MessageDisplay event." Preserve the NON-NEGOTIABLES section at the top.          | repo maintainer                | YES — paper-trail requirement per CLAUDE.md                                         |
| `.claude/skills/validate-hook/references/anthropic-hooks-reference.md` (or wherever the canonical hooks-reference lives) | Add `if:`, `args[]`, `continueOnBlock`, `defer`, `MessageDisplay`, `SessionStart.sessionTitle`, `SessionStart.reloadSkills` to the spec snapshot. Update validator logic to match.                                                                                              | validate-hook skill maintainer | NO — additive validator capability, current validator doesn't crash on these fields |
| `.claude/skills/validate-mcp/references/`                                                                                | Add `_meta["anthropic/maxResultSizeChars"]` annotation to MCP tool result spec snapshot.                                                                                                                                                                                        | validate-mcp skill maintainer  | NO — additive                                                                       |
| `.claude/skills/skill-creator/` interactive flow                                                                         | Offer `disallowed-tools` as an optional frontmatter field. Forge mode templates default-include conservative disallow list.                                                                                                                                                     | skill-creator maintainer       | NO — improves new skills, doesn't break existing                                    |
| `.claude/skills/agent-creator/`                                                                                          | No change to camelCase `disallowedTools` field. Add documentation note in the agent-vs-skill comparison about the parallel kebab-case `disallowed-tools` on skills.                                                                                                             | agent-creator maintainer       | NO                                                                                  |
| `.claude/skills/validate-plugin/` end-to-end runner                                                                      | Pick up the validate-skills-schema.py update transparently. No direct change needed.                                                                                                                                                                                            | n/a                            | n/a                                                                                 |
| Repo-level CLAUDE.md (`)                                                                                                 | Update the SKILL.md frontmatter spec section to mention `disallowed-tools` as schema 3.7.0+ optional field. Update the "Agents use disallowedTools (denylist); skills use allowed-tools (allowlist)" note to reflect that skills now ALSO support disallowed-tools in parallel. | repo maintainer                | YES — repo-level spec is the canonical source for plugin authors                    |
| `freshie/inventory.sqlite` schema                                                                                        | If the validator now produces a `disallowed_tools_count` or `disallowed_tools_present` column on `skill_compliance`, add it. Otherwise no change.                                                                                                                               | freshie maintainer             | NO — optional analytic column                                                       |

## Order of operations

1. **First (today/this week):** Update repo-level CLAUDE.md spec section + write the SCHEMA_CHANGELOG.md 3.7.0 entry. These are the canonical sources every plugin author references. They block accurate validator updates because the validator implements what the spec says.
2. **Second (this week):** Update `scripts/validate-skills-schema.py` to handle `disallowed-tools` at the schema layer. Bump `SCHEMA_VERSION` constant. Run against the full marketplace catalog and confirm no regressions.
3. **Third (this week or next):** Update the four validator skills (`validate-hook`, `validate-mcp`, `validate-skillmd`, `validate-plugin`) to accept the new fields without crashing or false-flagging.
4. **Fourth (next sprint):** Update the two creator skills (`skill-creator`, `agent-creator`) to offer the new fields in their interactive flows and templates.
5. **Fifth (opportunistic):** Audit-sweep existing 400+ plugins for opportunities to add `disallowed-tools`, migrate hooks to `if:` matchers, etc. Track in a follow-up bead but do not block on it.

## Downstream consumer references

This Decision Record is referenced from:

- `plugins/saas-packs/databricks-pack/000-docs/000-INDEX.md` — the databricks-pack rebuild references this for its hook implementations (Epics 4 + 6), its skill scaffolds (Epics 2-6 T1), its MCP integration (Epic 1 T4-T9), and its dual-surface helpers (Epic 1 T14).
- Future partner-integration listings reference the same platform features when their skills land.
- New plugins authored via `skill-creator --forge` from this date forward should be authored against schema 3.7.0, not 3.6.0.

## What this decision does NOT change

- The 8-field `ALWAYS_REQUIRED` set in `validate-skills-schema.py` (name, description, allowed-tools, version, author, license, compatibility, tags) remains the marketplace bar. `disallowed-tools` is additive and optional, not required.
- The IS enterprise rubric (100-point) and marketplace tier semantics remain intact.
- The brand-scrub policy remains intact (the changelog requires no branding changes).
- Existing plugins continue to validate cleanly. No deprecation, no breaking changes.

## Audit trail

- Supplements `000-docs/SCHEMA_CHANGELOG.md` (which is the authoritative schema version history)
- Cross-referenced from `plugins/saas-packs/databricks-pack/000-docs/000-INDEX.md` and the databricks-pack 013-AT-ADEC for the rebuild-specific implementation guidance
- Filing trigger: Jeremy's direct instruction 2026-05-27 — "the changelog applies to the whole fucking repo" (correcting an earlier scoping error where 014 was filed inside the databricks-pack folder)

## Acting head of board declaration

I, Claude (designated acting head of board by Jeremy Longshore on 2026-05-27), file this repo-wide Decision Record cataloging the Claude Code platform changelog impact on the entire Tons of Skills marketplace ecosystem. The catalog is implementation-guidance for repo maintainers + a canonical pointer for downstream consumers (databricks-pack rebuild, future partnerships, new skill authors). Specific code/schema changes follow this file as discrete PRs against `validate-skills-schema.py`, `SCHEMA_CHANGELOG.md`, the validator skills, and the creator skills.

- Jeremy Longshore
  intentsolutions.io
