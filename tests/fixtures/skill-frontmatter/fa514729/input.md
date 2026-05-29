---
name: validate-agent
description: |
  Validate a single Claude Code subagent file (agents/NAME.md) against the
  canonical Anthropic sub-agents spec. Checks YAML frontmatter for required
  fields (name, description), valid optional fields (tools allowlist,
  disallowedTools denylist, model, permissionMode, maxTurns, color enum,
  initialPrompt, etc.), rejects deprecated IS-extension fields (capabilities,
  expertise_level, activation_priority), and surfaces malformed YAML. Calls
  the Intent Solutions validator with the agents-only flag and interprets
  the output. Distinct from /agent-creator (which scaffolds new agents
  interactively) — this skill audits existing agent files. Use when reviewing
  a contributor's agent.md, auditing your own plugin's agents directory, or
  spot-checking an agent before merge. Trigger with "/validate-agent",
  "validate this agent", "check agent.md", "audit agent", "is this agent
  spec-correct".
allowed-tools: 'Read,Bash(python3:*),Bash(jq:*),Bash(grep:*),Glob,AskUserQuestion'
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; requires Python 3 + the IS validator script
tags: [validation, subagents, agents, plugin-quality, claude-code]
user-invocable: true
argument-hint: '[path-to-agent.md] [--strict]'
---

# Validate Agent

Schema validator for Claude Code subagent files. Reads `agents/<name>.md`, parses YAML frontmatter, and grades it against the [canonical Anthropic sub-agents spec](https://code.claude.com/docs/en/sub-agents). Anchors every claim in `references/anthropic-sub-agents-spec.md` so spec drift is detectable and recoverable.

## Overview

A Claude Code subagent is a single Markdown file with YAML frontmatter at `agents/<name>.md`. Two fields are required by the spec; the rest are optional but typed.

| Field             | Required | Notes                                                      |
| ----------------- | -------- | ---------------------------------------------------------- |
| `name`            | yes      | Kebab-case, unique within the plugin                       |
| `description`     | yes      | When-to-use phrasing for the dispatcher                    |
| `tools`           | no       | Allowlist (preferred) — array of valid tool names          |
| `disallowedTools` | no       | Denylist — array; ⚠ must be array, NOT string              |
| `model`           | no       | `inherit` / `sonnet` / `haiku` / `opus`                    |
| `permissionMode`  | no       | `default` / `acceptEdits` / `bypassPermissions` / `plan`   |
| `maxTurns`        | no       | Integer cap on agentic loop iterations                     |
| `effort`          | no       | `low` / `medium` / `high` / `xhigh` / `max`                |
| `skills`          | no       | Array of skill names available inside the agent            |
| `mcpServers`      | no       | Array of MCP server names available                        |
| `hooks`           | no       | Inline hook map (PreToolUse / Stop / etc.)                 |
| `memory`          | no       | Memory namespace                                           |
| `background`      | no       | Boolean — runs detached                                    |
| `isolation`       | no       | `worktree` for isolated git copy                           |
| `color`           | no       | Enum: red, blue, green, yellow, purple, orange, pink, cyan |
| `initialPrompt`   | no       | First-turn user message                                    |

**Deprecated IS-extension fields** (flag, don't accept silently): `capabilities`, `expertise_level`, `activation_priority`. These were never in any spec. The IS validator's `validate_agent` function (made spec-current in PR #705) is the source of truth.

This skill is a thin wrapper: it calls `python3 scripts/validate-skills-schema.py --agents-only <agent.md>`, parses the verdict, and presents it with verbatim spec citations. Distinct from `/agent-creator` (which interactively scaffolds new agents).

## Prerequisites

- Python 3 with `pyyaml` installed
- IS validator at `~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py` (v7.0+, schema 3.3.1)
- `jq` for any inline frontmatter inspection
- The spec snapshot under `references/anthropic-sub-agents-spec.md` (symlinked from `agent-creator/references/`)

## Instructions

### Step 1: Resolve target file

Argument forms:

- **Single agent file** — `/validate-agent /path/to/agents/my-agent.md`
- **Bare directory** — `/validate-agent /path/to/plugin/` → glob `agents/*.md` and validate each
- **Plugin root with `agents/`** — auto-discover

If multiple agents are found and the user passed a directory, audit each in turn. Cache results per file.

### Step 2: Frontmatter shape sanity (pre-flight)

Before invoking the IS validator, do a quick `jq`-based check for the obvious pitfalls — the IS validator catches them all but a fast pre-flight gives clearer error messages:

```bash
AGENT="<resolved-path>"

# Extract frontmatter (between leading --- and next ---)
FRONTMATTER=$(awk '/^---$/{c++; next} c==1' "$AGENT")

# Required fields
echo "$FRONTMATTER" | grep -qE '^name:' || echo "FAIL: missing required field 'name'"
echo "$FRONTMATTER" | grep -qE '^description:' || echo "FAIL: missing required field 'description'"

# disallowedTools must be array (common mistake: passing as string)
echo "$FRONTMATTER" | grep -qE '^disallowedTools:\s*\[' \
  && echo "  ✓ disallowedTools is array" \
  || (echo "$FRONTMATTER" | grep -q '^disallowedTools:' && echo "FAIL: disallowedTools must be a YAML array, e.g. [tool1, tool2]")

# color enum
COLOR=$(echo "$FRONTMATTER" | grep -E '^color:' | sed 's/color:\s*//' | tr -d '"' | tr -d "'")
if [ -n "$COLOR" ]; then
  case "$COLOR" in
    red|blue|green|yellow|purple|orange|pink|cyan) ;;
    *) echo "FAIL: color '$COLOR' not in valid enum (red/blue/green/yellow/purple/orange/pink/cyan)" ;;
  esac
fi

# Deprecated IS-extension fields
for deprecated in capabilities expertise_level activation_priority; do
  echo "$FRONTMATTER" | grep -qE "^${deprecated}:" \
    && echo "WARN: deprecated IS-extension field '$deprecated' — not in any canonical spec, removable"
done
```

### Step 3: IS validator (authoritative)

Run the validator and capture its verdict:

```bash
python3 ~/000-projects/claude-code-plugins/scripts/validate-skills-schema.py \
  --agents-only "$AGENT" 2>&1
```

The validator returns errors and warnings. Group them in the output report (Step 5). Examples of common findings:

- `ERROR: missing required field 'name'`
- `ERROR: 'disallowedTools' must be an array of strings, got string`
- `ERROR: 'color' value 'magenta' not in enum [red,blue,green,yellow,purple,orange,pink,cyan]`
- `WARN: 'capabilities' is a deprecated IS-extension field; not in any canonical spec`

### Step 4: Tools allowlist sanity

The `tools` field accepts the same tool name allowlist as skills. Cross-reference against the canonical list (Read, Write, Edit, Bash, Glob, Grep, WebFetch, WebSearch, Task, TodoWrite, NotebookEdit, AskUserQuestion, Skill). MCP-prefixed tools (`mcp__<server>__<name>`) are also valid:

```bash
TOOLS=$(echo "$FRONTMATTER" | grep -A1 '^tools:' | tail -1 | tr -d '[]' | tr ',' '\n')
for tool in $TOOLS; do
  tool=$(echo "$tool" | tr -d ' "'\''')
  case "$tool" in
    Read|Write|Edit|Bash*|Glob|Grep|WebFetch|WebSearch|Task|TodoWrite|NotebookEdit|AskUserQuestion|Skill) ;;
    mcp__*) ;;
    "") ;;
    *) echo "WARN: tool '$tool' not in canonical allowlist" ;;
  esac
done
```

### Step 5: Verdict

```
══════════════════════════════════════════════════════════════════════
  AGENT AUDIT — <agent-file>
══════════════════════════════════════════════════════════════════════

  Pre-flight (frontmatter shape):
    Required 'name':                    PASS
    Required 'description':             PASS
    'disallowedTools' shape:            PASS / FAIL — must be array
    'color' enum:                       PASS / FAIL — value '<x>' not in enum
    Deprecated fields:                  none / [capabilities, expertise_level]

  IS validator (--agents-only):
    Errors:    <count>
    Warnings:  <count>
    <verbatim error/warn lines>

  Tools allowlist:                      <N> tool(s), all canonical
  ──────────────────────────────────────────────────────────────────
  VERDICT: PASS | FAIL — <count> blocking issue(s)
  ──────────────────────────────────────────────────────────────────
```

**Block on**: missing `name` or `description`, malformed YAML, `disallowedTools` as string instead of array, `color` value outside enum.

**Warn (don't block)**: deprecated IS-extension fields, unknown tool name, missing optional polish fields.

**`--strict` mode**: promotes warnings to errors.

## Output

- **Console report** per Step 5 with PASS / FAIL verdict
- **Verbatim validator output** for transparency
- **Spec citations** linking to `references/anthropic-sub-agents-spec.md` and live canonical URL

## Error Handling

| Error                                         | Recovery                                                                                                |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Agent file not found                          | Use `Glob` to search `agents/*.md`; ask for clarification                                               |
| YAML parse error                              | Surface line number from `pyyaml`; recommend `python3 -c "import yaml; yaml.safe_load(open('<file>'))"` |
| Validator script missing                      | Report expected path; suggest cloning `claude-code-plugins-plus-skills`                                 |
| Validator returns warnings only               | Report PASS with warning count; don't escalate unless `--strict`                                        |
| Deprecated field present                      | Cite PR #705 + `references/anthropic-sub-agents-spec.md`; offer to draft removal patch                  |
| Multiple agents in directory                  | Audit each in turn; aggregate verdict at the end                                                        |
| Frontmatter missing entirely (no `---` block) | Surface as fatal — cannot validate without frontmatter                                                  |

## Examples

**Validate a single agent file**:

```
/validate-agent ~/000-projects/claude-code-plugins/plugins/productivity/plane/agents/plane-expert.md
```

**Validate every agent in a plugin's `agents/` directory**:

```
/validate-agent ~/000-projects/claude-code-plugins/plugins/productivity/plane/
```

**Strict mode (deprecated fields become errors)**:

```
/validate-agent /path/to/agents/my-agent.md --strict
```

**External-contributor PR audit (called by `/validate-plugin`)**:

```
/validate-agent /tmp/external-contributor/their-plugin/agents/their-agent.md
```

## Resources

### Canonical spec (saved verbatim in `references/`)

- `references/anthropic-sub-agents-spec.md` — full sub-agents reference
- `references/anthropic-example-subagents.md` — example agents from Anthropic docs

### Live canonical URLs

- [code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents) — sub-agents reference
- [code.claude.com/docs/en/plugins-reference#agents](https://code.claude.com/docs/en/plugins-reference#agents) — agents in the plugin manifest
- [PR #705](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/705) — agent validator made spec-current

### Related skills

- `/agent-creator` — interactively scaffolds new agents (this skill audits existing ones)
- `/validate-plugin` — orchestrator that delegates here for per-agent deep audits
- `/validate-skillmd` — sibling SKILL.md grader
- `/validate-mcp` / `/validate-hook` / `/validate-marketplace` — sibling component validators
