# Anthropic Skills Spec — Versioned Snapshot

**Snapshot ID**: 2026-05-07-initial
**Source**: https://code.claude.com/docs/en/skills
**Captured**: 2026-05-07
**Refresh cadence**: Quarterly (manual PR or scheduled cron)
**Read by**: JRig Tier 3A spec-compliance check (called from `/validate-skillmd --thorough`)

---

## Why this file exists

Tier 3A of `/validate-skillmd` validates SKILL.md frontmatter against Anthropic's official spec. We **do not live-fetch** that spec at validation time — rate-limit risk plus CI flakiness make live-fetch a bad gate. Instead, we capture the spec as a versioned snapshot here, refresh it quarterly via a dedicated PR, and let validation read this frozen reference.

The PR review on each refresh = the human gate that catches breaking spec changes BEFORE they hit thousands of skill validations.

---

## Required-field set (Anthropic spec floor)

Anthropic's published spec requires only these two fields:

- `name` — string, max 64 chars, lowercase + hyphens + numbers, no reserved words (`anthropic`, `claude`)
- `description` — string, max 1024 chars, third-person voice, must be non-empty

Every other field documented at `code.claude.com/docs/en/skills#frontmatter-reference` is optional under Anthropic's spec floor.

> **NOTE**: The IS marketplace tier requires 8 fields, not 2. That's the IS rubric sitting on top of Anthropic's spec — it doesn't change Anthropic's published requirements. See `000-docs/SCHEMA_CHANGELOG.md` § NON-NEGOTIABLES.

---

## Optional-field allow-list (with type validation)

| Field | Type | Notes |
|---|---|---|
| `allowed-tools` | comma-separated string OR space-separated string OR YAML list | All three forms accepted (per Anthropic doc verbatim). Paren-depth-aware tokenization for multi-word forms like `Bash(git add *)`. |
| `model` | string | `inherit` / `opus` / `sonnet` / `haiku` shorthand; full IDs accepted but not recommended |
| `effort` | enum | `low` / `medium` / `high` / `xhigh` / `max` |
| `argument-hint` | string | Autocomplete hint for `/`-invocation |
| `arguments` | string (space-separated) | Named positional args (`$arg1`, `$arg2`) |
| `paths` | comma-separated globs | Limits auto-activation to matching paths |
| `context` | enum | `fork` (run in subagent) |
| `agent` | string | Subagent type when `context: fork`; defaults to `general-purpose` |
| `user-invocable` | boolean | Default `true`; `false` hides from `/` menu |
| `disable-model-invocation` | boolean | Default `false`; `true` blocks Claude auto-activation |
| `hooks` | object | Skill-scoped lifecycle hooks |
| `shell` | enum | `bash` (default) / `powershell` |
| `when_to_use` | string | Combined cap with description = 1,536 chars |
| `metadata` | object | Free-form key-value (per agentskills.io) |
| `compatibility` | string (max 500 chars) | Free-text per agentskills.io |
| `license` | string | SPDX or human-readable |

---

## Documented substitution variables

These are replaced before Claude processes the skill body:

- `$ARGUMENTS` / `$0` / `$1` … `$9` — user-provided arguments
- `${CLAUDE_SESSION_ID}` — current session ID
- `${CLAUDE_SKILL_DIR}` — absolute path to the current skill's directory
- `${CLAUDE_PLUGIN_ROOT}` — absolute path to the plugin root (when skill is plugin-bundled)
- `${CLAUDE_PLUGIN_DATA}` — persistent plugin state directory (survives updates; v2.1.78+)
- `${CLAUDE_EFFORT}` — current effort level (added in schema 3.3.1)

---

## Dynamic Context Injection (DCI)

```markdown
!`shell-command`
```

- Output is injected verbatim into the skill body at activation time
- Always include a fallback for missing tools: `` !`tool --version 2>/dev/null || echo 'not installed'` ``
- Keep injections small — summaries, not full file dumps

---

## Refresh procedure

1. Fetch `https://code.claude.com/docs/en/skills` and `https://code.claude.com/docs/en/skills#frontmatter-reference` rendered HTML
2. Diff against current snapshot — identify added / removed / changed fields
3. Update sections above (required-field set, optional allow-list, substitution vars, DCI rules)
4. Bump Snapshot ID to `YYYY-MM-DD-NN`
5. Open PR with the diff
6. PR review checks: any required-field set change requires explicit IS architectural approval (see SCHEMA_CHANGELOG.md NON-NEGOTIABLES). Bug fixes that bring the IS validator into spec compliance can ship autonomously.
7. Merge → Tier 3A reads the new snapshot on next `--thorough` run

---

## Status

This is the **initial seed** snapshot, written 2026-05-07 against the Anthropic docs as understood at that date. A full structural refresh against the live published spec is the first task of the next quarterly cadence. The seed captures the same field facts the IS validator already enforces — it gives Tier 3A something concrete to compare against on day one.
