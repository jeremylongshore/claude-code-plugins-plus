---
name: validate-plugin
description: |
  Validate a Claude Code plugin directory end-to-end against the canonical Anthropic
  spec (manifest, skills, agents, commands, hooks, MCP servers, LSP, monitors,
  marketplace.json) AND the IS marketplace tier (8-field enterprise required-fields
  rubric + Tier 2 static production gate + optional JRig Tier 3 behavioral eval) AND
  cross-harness compatibility (Cursor, Windsurf, Codex CLI, Gemini CLI, Continue,
  Cline). Discovers each component the plugin contains and delegates per-component:
  SKILL.md to /validate-skillmd, agents to the agent validator, MCP servers + hooks +
  marketplace.json to inline schema validation against the canonical spec snapshots
  in references/. Use when reviewing an external-contributor PR, auditing your own
  plugin pre-submission, or auditing a plugin's multi-host claims. Trigger with
  "/validate-plugin", "validate this plugin", "audit external submission", "check
  plugin structure", "is this plugin ready to merge", "plugin spec compliance".
allowed-tools: 'Read,Bash(python3:*),Bash(j-rig:*),Bash(jq:*),Bash(git:*),Bash(find:*),Bash(ls:*),Bash(bash:*),Glob,AskUserQuestion,Skill'
version: 2.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; requires Python 3 + sqlite3 + jq; optionally j-rig CLI for Tier 3
tags:
  [
    validation,
    plugin-quality,
    marketplace,
    external-contributors,
    claude-code,
    cross-harness,
    governance,
  ]
user-invocable: true
argument-hint: '[plugin-dir-path|github-url|pr#] [--marketplace|--thorough]'
---

# Validate Plugin

End-to-end audit of a Claude Code plugin. Reads the [canonical Anthropic plugin spec](https://code.claude.com/docs/en/plugins-reference), discovers every component the plugin contains (skills, agents, commands, hooks, MCP servers, LSP servers, monitors, marketplace.json), and delegates per-component validation to the right tool. Anchors every claim in `references/` snapshots so spec drift is detectable + recoverable.

## Overview

A plugin can contain ten different component types per the [Anthropic plugins reference](https://code.claude.com/docs/en/plugins-reference). Most prior validators only audited one. This skill orchestrates the lot:

| Component           | Discovered at                                                         | Validator                                                                                                           |
| ------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Plugin manifest     | `.claude-plugin/plugin.json`                                          | inline (manifest schema in `references/anthropic-plugins-reference.md`)                                             |
| Skills              | `skills/<name>/SKILL.md`                                              | **delegate to `/validate-skillmd`** (Tier 0/1/2/3)                                                                  |
| Commands (legacy)   | `commands/*.md`                                                       | inline (treats as flat-skill format per Anthropic legacy guidance)                                                  |
| Agents              | `agents/<name>.md`                                                    | **delegate to `/validate-agent`** (frontmatter + IS validator `--agents-only`); deep authoring via `/agent-creator` |
| Hooks               | `hooks/hooks.json`                                                    | **delegate to `/validate-hook`** (event allowlist + handler shape + matcher regex compilability)                    |
| MCP servers         | `.mcp.json` or `plugin.json` `mcpServers` field                       | **delegate to `/validate-mcp`** (transport-specific schema, credential hygiene)                                     |
| LSP servers         | `.lsp.json`                                                           | inline (lighter validation — schema in plugins-reference)                                                           |
| Monitors            | `monitors/monitors.json`                                              | inline                                                                                                              |
| Default settings    | `settings.json`                                                       | inline (only `agent` and `subagentStatusLine` keys supported)                                                       |
| Marketplace catalog | `.claude-plugin/marketplace.json` (when plugin is also a marketplace) | **delegate to `/validate-marketplace`** (catalog schema, source resolution, optional `--deep` per-entry walk)       |

Plus four cross-cutting audits:

- **IS marketplace tier** — 8-field enterprise required-set + 100-point rubric (per SKILL.md, via `/validate-skillmd`)
- **Tier 2 production gate** — 5 inline checks (security/correctness alongside the rubric)
- **Tier 3 behavioral eval** — JRig 7-layer (opt-in via `--thorough`)
- **Cross-harness compatibility** — Cursor / Windsurf / Codex / Gemini / Continue / Cline per `references/cross-harness-compatibility.md`

The skill produces one unified merge-readiness report.

## Prerequisites

- Python 3 with `pyyaml` (for `validate-skills-schema.py`)
- `jq` (for plugin.json + marketplace.json inspection)
- `sqlite3` (for any Freshie-backed audits)
- IS validator at `~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py` (v7.0+, schema 3.3.1)
- `j-rig` CLI on PATH (optional; only needed for `--thorough` Tier 3)
- Sibling skill `/validate-skillmd` available (delegated to for per-SKILL.md deep grading)

## Instructions

### Step 1: Resolve target plugin

Argument forms:

- **Local path** — `/validate-plugin /path/to/plugin/`
- **GitHub URL** — `/validate-plugin https://github.com/owner/repo` → clone to `/tmp/plugin-validate-<repo>/`, walk for plugin layout
- **PR number on claude-code-plugins-plus-skills** — `/validate-plugin 679` → fetch upstream repo URL from sources.yaml diff, clone, audit

If unclear, use AskUserQuestion to disambiguate. Cache as `$PLUGIN_DIR`.

### Step 1.5: Pre-flight — spec snapshot freshness

Before grading the plugin, confirm the references this skill (and the four sibling validators) grade against are not stale. Run the freshness checker:

```bash
bash ~/.claude/skills/validate-plugin/scripts/check-spec-freshness.sh --days 90
```

Default threshold is **90 days**. If anything comes back STALE, surface it at the top of the audit report — the verdict is still emitted but the user knows the rules may have drifted. The refresh procedure lives in `references/README.md`.

A stale snapshot does NOT block the audit. It's a warning so the verdict is read with the right caveat. If the user wants to refresh first, they re-fetch the listed Source URLs and bump the `Captured:` dates per `references/README.md`.

### Step 2: Layer 0 — Component discovery

Walk the plugin directory and inventory which components are present. Produce a structured map for downstream delegation:

```bash
PLUGIN_DIR=<resolved-path>

echo "──── Plugin manifest ────"
[ -f "$PLUGIN_DIR/.claude-plugin/plugin.json" ] && echo "  ✓ canonical .claude-plugin/plugin.json" \
  || echo "  ✗ missing canonical manifest"

# Top-level legacy plugin.json (wrong location)
[ -f "$PLUGIN_DIR/plugin.json" ] && echo "  ! plugin.json at top level (Claude Code's loader won't find it here)"

# Marketplace catalog (only if plugin is also a marketplace)
[ -f "$PLUGIN_DIR/.claude-plugin/marketplace.json" ] && echo "  ✓ marketplace.json (this plugin distributes others)"

echo ""
echo "──── Components present ────"
SKILLS=$(find "$PLUGIN_DIR/skills" -name "SKILL.md" -type f 2>/dev/null | wc -l)
AGENTS=$(find "$PLUGIN_DIR/agents" -name "*.md" -type f 2>/dev/null | wc -l)
COMMANDS=$(find "$PLUGIN_DIR/commands" -name "*.md" -type f 2>/dev/null | wc -l)
HOOKS=$([ -f "$PLUGIN_DIR/hooks/hooks.json" ] && echo "1" || echo "0")
MCP=$([ -f "$PLUGIN_DIR/.mcp.json" ] && echo "1" || echo "0")
LSP=$([ -f "$PLUGIN_DIR/.lsp.json" ] && echo "1" || echo "0")
MONITORS=$([ -f "$PLUGIN_DIR/monitors/monitors.json" ] && echo "1" || echo "0")
SETTINGS=$([ -f "$PLUGIN_DIR/settings.json" ] && echo "1" || echo "0")

echo "  Skills:        $SKILLS"
echo "  Agents:        $AGENTS"
echo "  Commands:      $COMMANDS (legacy)"
echo "  Hooks:         $([ "$HOOKS" = "1" ] && echo present || echo absent)"
echo "  MCP servers:   $([ "$MCP" = "1" ] && echo present || echo absent)"
echo "  LSP servers:   $([ "$LSP" = "1" ] && echo present || echo absent)"
echo "  Monitors:      $([ "$MONITORS" = "1" ] && echo present || echo absent)"
echo "  Settings:      $([ "$SETTINGS" = "1" ] && echo present || echo absent)"

echo ""
echo "──── Cross-harness artifacts ────"
[ -d "$PLUGIN_DIR/.cursor" ] && echo "  ✓ .cursor/ (Cursor MCP / rules)"
[ -f "$PLUGIN_DIR/.cursorrules" ] && echo "  ✓ .cursorrules (Cursor legacy rules)"
[ -d "$PLUGIN_DIR/.windsurf" ] && echo "  ✓ .windsurf/"
[ -f "$PLUGIN_DIR/.windsurfrules" ] && echo "  ✓ .windsurfrules"
[ -d "$PLUGIN_DIR/.codex" ] && echo "  ✓ .codex/"
[ -f "$PLUGIN_DIR/AGENTS.md" ] && echo "  ✓ AGENTS.md (Codex CLI)"
[ -f "$PLUGIN_DIR/GEMINI.md" ] && echo "  ✓ GEMINI.md"
[ -f "$PLUGIN_DIR/.github/copilot-instructions.md" ] && echo "  ✓ .github/copilot-instructions.md (VS Code Copilot)"
```

The component inventory drives every downstream step. Report it cleanly.

### Step 3: Layer 1 — Plugin manifest validation

Validate `plugin.json` against the [canonical schema](https://code.claude.com/docs/en/plugins-reference). Read the saved snapshot at `references/anthropic-plugins-reference.md` for the field-by-field rules.

```bash
MANIFEST="$PLUGIN_DIR/.claude-plugin/plugin.json"
[ ! -f "$MANIFEST" ] && [ -f "$PLUGIN_DIR/plugin.json" ] && MANIFEST="$PLUGIN_DIR/plugin.json"

# JSON validity
jq empty "$MANIFEST" 2>&1

# Required fields per spec
jq '. | {
  name: .name,
  description: .description,
  version: .version,
  author: .author,
  has_repository: (.repository | type == "string"),
  has_license: (.license | type == "string"),
  components_declared: (
    [.commands, .agents, .skills, .hooks, .mcpServers, .outputStyles, .lspServers]
    | map(select(. != null))
    | length
  )
}' "$MANIFEST"
```

**Required**: `name` (always), per the spec. **Recommended for marketplace listing**: `version`, `description`, `author`, `repository`, `license`, `keywords`. Component path fields (`commands`, `agents`, `skills`, `hooks`, `mcpServers`, `outputStyles`, `lspServers`) are optional — Claude Code auto-discovers from the standard directory layout when omitted.

**Block on**: malformed JSON, missing `name`, manifest at wrong location (top-level instead of `.claude-plugin/`).

### Step 4: Layer 2 — Per-component validation (delegation)

For each component type discovered in Step 2, run the right validator.

#### 4a. Skills → delegate to `/validate-skillmd`

For every `skills/<name>/SKILL.md` found, invoke the sibling skill `/validate-skillmd --marketplace`. This produces:

- Tier 1 grade (100-point IS rubric)
- Tier 2 production gate verdict (5 inline checks)
- Tier 3 behavioral eval (when `--thorough` passed through)

Two invocation patterns:

- **Bash path** (deterministic, no agent dispatch):

  ```bash
  for skill in $(find "$PLUGIN_DIR/skills" -name "SKILL.md" -type f); do
    echo "─── $(basename $(dirname $skill)) ───"
    python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py \
      --marketplace "$skill"
  done
  ```

- **Skill path** (delegates to `/validate-skillmd` for nuanced grading + auto-fix offers):
  Use the `Skill` tool with `command: "validate-skillmd"` and the SKILL.md path as argument. The sibling skill handles Tiers 0–3 + offers fix recommendations.

Default to the Bash path for batch audits; switch to the Skill path when the user wants per-skill polish work after the audit.

#### 4b. Agents → delegate to `/validate-agent`

For every `agents/*.md` discovered, invoke `/validate-agent` per file (or pass the directory and let it batch). The sibling skill calls `validate-skills-schema.py --agents-only` under the hood and adds frontmatter pre-flight checks (color enum, deprecated-field detection, tool allowlist).

```bash
for agent in $(find "$PLUGIN_DIR/agents" -name "*.md" -type f 2>/dev/null); do
  echo "─── $(basename "$agent") ───"
  # Bash-path equivalent (when not using the Skill tool):
  python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py \
    --agents-only "$agent" 2>&1 | grep -E "ERROR|WARN" | head -10
done
```

The agent validator was made spec-current in PR #705 (color enum, initialPrompt, permissionMode auto). For deep authoring help (creating new agents from scratch), suggest `/agent-creator`. For per-agent grading deep-dive, use `/validate-agent <agent.md> --strict`.

#### 4c. Commands (legacy) → inline format check

Plugins shipped before the `skills/` convention used `commands/*.md` as flat markdown files. Anthropic still loads them; new plugins should use `skills/`. Inline-validate frontmatter only (no body grading):

```bash
for cmd in $(find "$PLUGIN_DIR/commands" -name "*.md" -type f 2>/dev/null); do
  python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py \
    --commands-only "$cmd" 2>&1 | grep -E "ERROR" | head -5
done
```

If commands are present, surface a recommendation to migrate them to `skills/` per Anthropic's [plugins overview](https://code.claude.com/docs/en/plugins) ("Use `skills/` for new plugins").

#### 4d. Hooks → delegate to `/validate-hook`

If `hooks/hooks.json` exists (or a `hooks:` block lives in `settings.json`), invoke `/validate-hook "$PLUGIN_DIR/hooks/hooks.json"`. The sibling enforces 3-level nesting, the ~30-event allowlist, per-handler required fields by type (command/http/mcp_tool/prompt/agent), matcher regex compilability, and the `PreToolUse` exit-code-2 documentation check.

#### 4e. MCP servers → delegate to `/validate-mcp`

If `.mcp.json` exists (or `mcpServers` is declared inline in `plugin.json`), invoke `/validate-mcp <file>`. The sibling enforces transport-required fields (stdio: `command`; http/sse/ws: `url`), server-name uniqueness + kebab-case, sub-object types (args=array, env=object, headers=object), and credential hygiene (plaintext-secret patterns in `env` values; `--strict` promotes to errors).

For runtime correctness (do the tools the server advertises match what the plugin's docs claim?), recommend running the MCP server itself in dev mode — the validator audits schema, not behavior.

#### 4f. LSP servers → inline schema check

Read `.lsp.json`:

```bash
[ -f "$PLUGIN_DIR/.lsp.json" ] && jq '.' "$PLUGIN_DIR/.lsp.json"
```

Each language server: `command` + `args` + `extensionToLanguage` map. Lighter validation — full schema in [plugins-reference](https://code.claude.com/docs/en/plugins-reference#lsp-servers).

#### 4g. Monitors → inline schema check

Read `monitors/monitors.json`:

```bash
jq '.[] | {name: .name, command: .command, description: .description}' \
  "$PLUGIN_DIR/monitors/monitors.json" 2>/dev/null
```

Each entry: `name`, `command`, optional `description`, optional `when` trigger. Schema in [plugins-reference#monitors](https://code.claude.com/docs/en/plugins-reference#monitors).

#### 4h. Settings → inline check

Read `settings.json` at plugin root. Only `agent` and `subagentStatusLine` keys are supported by Claude Code's plugin settings loader. Other keys are silently ignored — flag as a warning if present (won't error but author is probably confused about what `settings.json` does in a plugin context).

#### 4i. Marketplace catalog → delegate to `/validate-marketplace` (only when present)

If the plugin (or repo) ships `.claude-plugin/marketplace.json`, invoke `/validate-marketplace <file>`. The sibling enforces top-level required fields (`name`, `owner.name`, `plugins[]`), per-entry required fields (`name`, `source`), and source-type handling (relative path resolves on disk, github shorthand parses, full URLs accepted). Pass `--deep` to walk every `./plugins/<dir>` entry and reverse-delegate to `/validate-plugin`.

### Step 5: Layer 3 — Cross-harness compatibility audit

For plugins that claim multi-host support (per their README badge or marketplace.extended.json description), verify each claim against `references/cross-harness-compatibility.md`:

```bash
echo "──── Cross-harness wiring audit ────"

# README claim parsing
README_HOSTS=$(grep -oE '(Claude Code|Claude Desktop|Cursor|Windsurf|Codex|Gemini|Continue|Cline)' \
  "$PLUGIN_DIR/README.md" 2>/dev/null | sort -u)
echo "  Hosts claimed in README: $README_HOSTS"
echo ""

# Per-host artifact checks
for host_artifact in \
  "Claude Code:.claude-plugin/plugin.json" \
  "Cursor:.cursor/mcp.json" \
  "Cursor:.cursorrules" \
  "Windsurf:.windsurfrules" \
  "Codex CLI:AGENTS.md" \
  "Gemini CLI:GEMINI.md" \
  "VS Code Copilot:.github/copilot-instructions.md"; do
  host=$(echo "$host_artifact" | cut -d: -f1)
  artifact=$(echo "$host_artifact" | cut -d: -f2)
  [ -e "$PLUGIN_DIR/$artifact" ] && echo "  ✓ $host: $artifact"
done
```

If the README claims a host but the corresponding artifact is absent AND there's no install script handling the wiring, surface as a "claim outpaces implementation" warning. Don't block — many plugins legitimately rely on install scripts.

### Step 6: Layer 4 — JRig Tier 3 behavioral eval (opt-in via `--thorough`)

Default invocations skip Tier 3. When `--thorough` is passed:

```bash
# Tier 3A — package integrity (deterministic, fast, free)
for skill_dir in $(find "$PLUGIN_DIR/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null); do
  j-rig check "$skill_dir" --json 2>&1
done

# Tier 3B — 7-layer behavioral eval (slow + costs $2-5/skill)
for skill_dir in $(find "$PLUGIN_DIR/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null); do
  j-rig eval "$skill_dir" \
    --models haiku,sonnet,opus \
    --db ~/000-projects/claude-code-plugins/freshie/inventory.sqlite \
    --json
done
```

If `j-rig` is not on PATH, emit a one-line install hint and skip Tier 3 silently (don't block):

```
JRig not on PATH. To enable Tier 3:
  cd ~/000-projects/j-rig-binary-eval/packages/cli && pnpm build && \
  ln -sf $PWD/dist/index.js ~/.local/bin/j-rig
```

### Step 7: Unified merge-readiness report

Combine every layer into one structured report:

```
══════════════════════════════════════════════════════════════════════
  PLUGIN AUDIT — <plugin-name> v<version>
══════════════════════════════════════════════════════════════════════

  Layer 0 — Component discovery
    Manifest at canonical path:           PASS / FAIL
    Skills:                               <N> found
    Agents:                               <N> found
    Commands (legacy):                    <N> found
    Hooks / MCP / LSP / Monitors:         <list>
    Cross-harness artifacts:              <list>

  Layer 1 — Plugin manifest
    JSON validity:                        PASS / FAIL
    Required `name`:                      PASS / FAIL
    Manifest at .claude-plugin/:          PASS / FAIL

  Layer 2 — Per-component validation
    Skills (via /validate-skillmd):
      <skill-name>:                       GRADE: A (95/100), Tier 2 GREEN
      <skill-name>:                       GRADE: D (65/100), Tier 2 RED — tool-safety
    Agents:
      <agent>.md:                         OK / <error count>
    Hooks (hooks.json):                   PASS / <error>
    MCP servers:                          <count>, <transports>
    Marketplace catalog:                  N/A or PASS / FAIL

  Layer 3 — Cross-harness
    Hosts claimed in README:              <list>
    Hosts with artifacts present:         <list>
    Claim vs reality:                     ALIGNED / GAP

  Layer 4 — JRig (opt-in --thorough)
    Package integrity per skill:          <results>
    Behavioral eval (Haiku/Sonnet/Opus):  <results> / SKIPPED

  ══════════════════════════════════════════════════════════════════════
  VERDICT: <READY TO MERGE | BLOCKED ON: <list> | NEEDS POLISH>
  ══════════════════════════════════════════════════════════════════════
```

Verdict logic:

- **READY TO MERGE**: Layer 0 manifest at canonical path, Layer 2 every skill ≥ Grade B with no Tier 2 errors, Layer 3 cross-harness claims aligned (or no multi-host claim made)
- **BLOCKED**: any Layer 0 missing canonical manifest, any Layer 2 Tier 2 ERROR, malformed JSON anywhere, any agent invalid-field error
- **NEEDS POLISH**: Layer 0 PASS, skills at Grade C-D, only Tier 2 warnings (not errors), cross-harness claim outpaces implementation — author's choice to ship as-is or polish

### Step 8: Generate review-comment draft (optional)

When the plugin is from an external-contributor PR, offer to draft the review. Use AskUserQuestion:

> The audit found <N> blocking issues + <M> warnings. Want me to draft a review for the PR + an educational issue on the contributor's repo? (Bigger submissions justify the upstream issue; smaller ones just need the PR comment.)

If yes, the draft should:

- Lead with what's correct (Layer 0/1 passes, Tier 2 GREENs)
- Name each blocking issue with validator output verbatim AND remediation path (with both Bash-scope and Safety-Justification options for Tier 2 tool-safety, etc.)
- Reference canonical Anthropic docs for spec questions ([code.claude.com/docs/en/plugins-reference](https://code.claude.com/docs/en/plugins-reference), [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills), [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents), [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp), [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks))
- Reference [agentskills.io/specification](https://agentskills.io/specification) for the open SKILL.md spec
- Reference [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification) for MCP-related findings
- Offer "you fix it / I fix it" choice
- For substantial submissions, generate the long-form educational version as an issue on THEIR repo (examples: [aomi-labs/skills#14](https://github.com/aomi-labs/skills/issues/14), [polyxmedia/mnemos#1](https://github.com/polyxmedia/mnemos/issues/1))
- End with the IS attribution footer per `~/.claude/CLAUDE.md` rule

## Output

The skill produces:

- **Console report**: layered audit per Step 7 with merge-readiness verdict
- **Optional review-comment draft**: PR-comment shape, focused on merge-blockers
- **Optional educational-issue draft**: longer walkthrough for substantial contributions
- **Source citations**: every spec-grounded claim links to the canonical Anthropic / AgentSkills.io / MCP source via the saved snapshots

## Error Handling

| Error                                                       | Recovery                                                                                                                                              |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Plugin directory not found                                  | Suggest `Glob` to find right path or ask user to paste it                                                                                             |
| Multiple SKILL.md locations (top-level + canonical)         | Surface all paths, ask user which is canonical, validate that one                                                                                     |
| Validator script missing                                    | Report expected path; suggest cloning `claude-code-plugins-plus-skills`                                                                               |
| `j-rig` not on PATH                                         | Emit install hint (one line); skip Tier 3 silently                                                                                                    |
| Plugin.json malformed JSON                                  | Surface `jq` parse error verbatim with line number                                                                                                    |
| Hooks.json invalid event name                               | Cross-reference `references/anthropic-hooks-reference.md` event allowlist                                                                             |
| MCP server missing transport field                          | Default is stdio per spec; flag if `command` also missing                                                                                             |
| Cross-harness claim with no artifacts AND no install script | Warning, not error — many plugins use runtime install scripts                                                                                         |
| Snapshot drift (validator says X, references say Y)         | Read snapshots verbatim — they're the source of truth per [issue #612](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/612) |

## Examples

**External-contributor PR audit (most common use)**:

```
/validate-plugin /tmp/external-contributor/their-plugin/
```

Walks all 9 component types, delegates to `/validate-skillmd` per SKILL.md, reports merge-readiness, offers PR-comment + upstream-issue drafts.

**Pre-submission self-check before forging**:

```
/validate-plugin plugins/productivity/my-new-plugin/
```

Same audit, in-repo. Useful as a final gate before opening a marketplace PR.

**Production-grade audit with JRig**:

```
/validate-plugin plugins/productivity/plane/ --thorough
```

Adds JRig 7-layer behavioral eval. Slow (~10–30 min/skill) + costs $2–5/skill. Right when promoting a plugin to JRig-Verified marketplace badge.

**Audit a GitHub repo + check multi-host claim**:

```
/validate-plugin https://github.com/aomi-labs/skills
```

Skill clones to `/tmp/`, walks the repo, picks canonical plugin directory (e.g. `plugins/aomi/`), runs full audit including cross-harness compatibility check against the README's "Works with Claude Code · Cursor · Gemini · Copilot" claim.

**Audit by PR number on the marketplace repo**:

```
/validate-plugin 679
```

Resolves PR #679 via `gh pr view`, parses the sources.yaml diff for upstream-repo URL, clones, audits.

## Resources

### IS-side governance

- [Issue #612](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/612) — pinned governance issue; non-negotiables + dance-prevention; **read before proposing validator changes**
- [`scripts/validate-skills-schema.py`](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/blob/main/scripts/validate-skills-schema.py) — IS validator (v7.0, schema 3.3.1)
- Sibling validators (delegated to per component): `/validate-skillmd` (skills, Step 4a), `/validate-agent` (agents, 4b), `/validate-hook` (hooks, 4d), `/validate-mcp` (MCP, 4e), `/validate-marketplace` (catalog, 4i); `/agent-creator` for from-scratch agent authoring
- Local script `scripts/check-spec-freshness.sh` — Step 1.5 pre-flight that flags reference snapshots older than 90 days; refresh procedure in `references/README.md`

### Anthropic canonical docs (saved verbatim in `references/`)

- `references/anthropic-plugins-overview.md` — plugin overview
- `references/anthropic-plugins-reference.md` — manifest + component schemas (62KB)
- `references/anthropic-plugin-marketplaces.md` — marketplace.json schema (55KB)
- `references/anthropic-mcp.md` — Claude Code MCP integration (60KB)
- `references/anthropic-hooks-reference.md` — hooks events + schemas
- Plus the spec snapshots already in `~/000-projects/claude-code-plugins/000-docs/`:
  - `anthropic-skills-spec-snapshot.md`
  - `agentskills-spec-snapshot.md`

### Open-spec references

- `references/mcp-open-spec.md` — MCP cross-host protocol (modelcontextprotocol.io)

### Cross-harness compatibility

- `references/cross-harness-compatibility.md` — Cursor, Windsurf, Codex CLI, Gemini CLI, Continue, Cline conventions

### Live canonical URLs (for spot-checks against the snapshots)

- [code.claude.com/docs/en/plugins](https://code.claude.com/docs/en/plugins) — plugin authoring
- [code.claude.com/docs/en/plugins-reference](https://code.claude.com/docs/en/plugins-reference) — manifest schema
- [code.claude.com/docs/en/plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) — marketplace distribution
- [code.claude.com/docs/en/skills](https://code.claude.com/docs/en/skills) — skills reference
- [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents) — agents reference
- [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) — Claude Code MCP integration
- [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks) — hooks reference
- [agentskills.io/specification](https://agentskills.io/specification) — open SKILL.md spec
- [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification) — open MCP spec

### Examples in the wild (this skill produced these)

- [aomi-labs/skills#14](https://github.com/aomi-labs/skills/issues/14) — educational issue covering Tier 2 security gate + 8-field rubric for an external contributor
- [polyxmedia/mnemos#1](https://github.com/polyxmedia/mnemos/issues/1) — educational issue covering plugin packaging + cross-harness layout for a multi-host product
- [PR #680 review on claude-code-plugins-plus-skills](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/680#issuecomment-4407418080) — corrected review comment after agent-validator fix
