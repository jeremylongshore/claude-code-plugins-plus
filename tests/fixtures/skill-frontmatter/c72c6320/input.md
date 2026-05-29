---
name: validate-mcp
description: |
  Validate a .mcp.json file (or the mcpServers field of a plugin.json) against
  the canonical Anthropic Claude Code MCP integration spec and the open
  Model Context Protocol spec. Checks JSON validity, transport-specific required
  fields (stdio needs command; http/sse/ws need url), unknown transport types,
  server-name uniqueness + kebab-case convention, and plaintext-credential
  hygiene in env values. Produces a per-server pass/fail report with verbatim
  spec citations. Distinct from /validate-plugin (which discovers components
  and orchestrates) — this skill grades one MCP config file in depth. Use when
  reviewing an external contributor's MCP server config, auditing your own
  plugin's .mcp.json, or spot-checking a server entry inside a plugin.json
  mcpServers block. Trigger with "/validate-mcp", "validate this MCP server",
  "check .mcp.json", "audit MCP config", "is this MCP config spec-correct".
allowed-tools: 'Read,Bash(jq:*),Bash(grep:*),Glob,AskUserQuestion'
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; requires jq on PATH
tags: [validation, mcp, model-context-protocol, plugin-quality, claude-code]
user-invocable: true
argument-hint: '[path-to-.mcp.json | path-to-plugin.json] [--strict]'
---

# Validate MCP

Schema validator for Claude Code MCP server configuration. Reads `.mcp.json` (or the inline `mcpServers` field in a `plugin.json`) and grades it against the [canonical Anthropic MCP integration spec](https://code.claude.com/docs/en/mcp) plus the open [Model Context Protocol spec](https://modelcontextprotocol.io/specification). Anchors every claim in `references/anthropic-mcp.md` + `references/mcp-open-spec.md` so spec drift is detectable and recoverable.

## Overview

A Claude Code plugin or workspace can declare MCP servers in two places:

1. **`.mcp.json`** at plugin root — top-level object mapping `<server-name>` → server-config
2. **`plugin.json`** — the same shape under the `mcpServers` field

Both follow the same schema. This skill validates either form against the spec snapshots and produces a per-server verdict (PASS / FAIL with explicit reason).

| Transport                           | Required  | Optional                       |
| ----------------------------------- | --------- | ------------------------------ |
| `stdio` (default if `type` omitted) | `command` | `args` (array), `env` (object) |
| `http`                              | `url`     | `headers` (object)             |
| `sse`                               | `url`     | `headers` (object)             |
| `ws`                                | `url`     | `headers` (object)             |

Server names should be unique within the file and kebab-case by convention. Plaintext credential patterns in `env` values are flagged as warnings (recommend env-var indirection like `${SECRET_NAME}`).

## Prerequisites

- `jq` on PATH (every check pipes through `jq`)
- Read access to the target `.mcp.json` or `plugin.json`
- The two spec snapshots under `references/` (symlinked from `validate-plugin/references/`)

## Instructions

### Step 1: Resolve target file

Argument forms:

- **Local `.mcp.json`** — `/validate-mcp /path/to/plugin/.mcp.json`
- **Local `plugin.json`** with inline servers — `/validate-mcp /path/to/plugin/.claude-plugin/plugin.json`
- **Bare directory** — `/validate-mcp /path/to/plugin/` → look for `.mcp.json` first, then `.claude-plugin/plugin.json` `mcpServers` field

If both forms are present, use AskUserQuestion to disambiguate. Cache the resolved file as `$MCP_FILE` and the JSON path that holds the server map as `$JQ_PATH` (`.` for `.mcp.json`, `.mcpServers` for `plugin.json`).

### Step 2: JSON validity + structural shape

```bash
MCP_FILE="<resolved>"
JQ_PATH="<. or .mcpServers>"

jq empty "$MCP_FILE" 2>&1 || { echo "FAIL: malformed JSON"; exit 1; }

# Must be an object mapping server-name → config
SHAPE=$(jq -r "$JQ_PATH | type" "$MCP_FILE")
[ "$SHAPE" = "object" ] || echo "FAIL: $JQ_PATH must be an object, got $SHAPE"

# Server count + names
jq -r "$JQ_PATH | keys[]" "$MCP_FILE"
```

### Step 3: Per-server schema check

For every server entry, verify transport-specific required fields:

```bash
jq -r "
  $JQ_PATH | to_entries[] |
  \"\\(.key)|\\(.value.type // \\\"stdio\\\")|\\(.value.command // \\\"\\\")|\\(.value.url // \\\"\\\")\"
" "$MCP_FILE" | while IFS='|' read -r name type command url; do
  case "$type" in
    stdio)
      [ -n "$command" ] || echo "FAIL $name: stdio transport requires 'command'"
      ;;
    http|sse|ws)
      [ -n "$url" ] || echo "FAIL $name: $type transport requires 'url'"
      ;;
    *)
      echo "FAIL $name: unknown transport type '$type' (allowed: stdio, http, sse, ws)"
      ;;
  esac
done
```

### Step 4: Naming + uniqueness checks

```bash
# Duplicate names (impossible at JSON-object level — jq retains last value — but flag if input has any)
# kebab-case convention (warn only)
jq -r "$JQ_PATH | keys[]" "$MCP_FILE" | while read -r name; do
  echo "$name" | grep -qE '^[a-z][a-z0-9-]*$' || echo "WARN $name: not kebab-case (recommended convention)"
done
```

### Step 5: Credential hygiene (env values)

Plaintext-looking secrets in `env` values are a common authoring slip. Warn (don't block) on values that look like API keys, tokens, or passwords pasted directly:

```bash
jq -r "
  $JQ_PATH | to_entries[] |
  select(.value.env != null) |
  .key as \$srv |
  .value.env | to_entries[] |
  \"\\(\$srv)|\\(.key)|\\(.value)\"
" "$MCP_FILE" | while IFS='|' read -r srv key value; do
  # Flag values that don't look like ${VAR} references
  if echo "$value" | grep -qvE '^\$\{[A-Z_][A-Z0-9_]*\}$'; then
    # And look like a high-entropy secret (heuristic: 20+ chars of [A-Za-z0-9_-])
    if echo "$value" | grep -qE '^[A-Za-z0-9_-]{20,}$'; then
      echo "WARN $srv.env.$key: looks like a plaintext secret — use \${VAR} indirection"
    fi
  fi
done
```

In `--strict` mode promote these warnings to errors.

### Step 6: Args + headers shape

```bash
# args must be an array if present
jq -r "
  $JQ_PATH | to_entries[] |
  select(.value.args != null and (.value.args | type) != \"array\") |
  \"FAIL \\(.key): args must be an array\"
" "$MCP_FILE"

# env must be an object if present
jq -r "
  $JQ_PATH | to_entries[] |
  select(.value.env != null and (.value.env | type) != \"object\") |
  \"FAIL \\(.key): env must be an object\"
" "$MCP_FILE"

# headers must be an object if present
jq -r "
  $JQ_PATH | to_entries[] |
  select(.value.headers != null and (.value.headers | type) != \"object\") |
  \"FAIL \\(.key): headers must be an object\"
" "$MCP_FILE"
```

### Step 7: Verdict

- **PASS** — every server has its transport-required field; no unknown transports; all sub-objects have correct types
- **WARN** — kebab-case violations, plaintext-secret patterns (non-strict mode)
- **FAIL** — any malformed JSON, any missing transport-required field, any unknown transport type, any wrong-typed sub-field, plaintext secrets in `--strict` mode

## Output

```
══════════════════════════════════════════════════════════════════════
  MCP CONFIG AUDIT — <file-path>
══════════════════════════════════════════════════════════════════════

  JSON validity:                              PASS
  Top-level shape:                            object (PASS)
  Servers declared:                           <N>

  Per-server verdicts:
    <name>  transport=<stdio|http|sse|ws>     PASS
    <name>  transport=stdio                   FAIL — missing 'command'
    <name>  transport=http                    PASS
    <name>  transport=sse                     WARN — name not kebab-case

  Credential hygiene:
    <server>.env.<KEY>                        WARN — plaintext-looking value

  ──────────────────────────────────────────────────────────────────
  VERDICT: PASS | FAIL — <count> blocking issue(s)
  ──────────────────────────────────────────────────────────────────
```

## Error Handling

| Error                                                            | Recovery                                                                               |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Target file not found                                            | Use `Glob` to search for `.mcp.json` under the given path; ask for clarification       |
| Both `.mcp.json` and inline `mcpServers` present                 | Use AskUserQuestion to pick which to validate (or run twice)                           |
| `jq: error (at <path>)`                                          | Surface the jq parse error verbatim with line number; recommend `jq empty` for re-test |
| Unknown transport `type`                                         | Cite `references/anthropic-mcp.md` allowlist (stdio/http/sse/ws); suggest correction   |
| Plaintext-secret pattern matched but value is a real placeholder | Author can suppress per-key by adopting `${VAR}` form; `--strict` makes this blocking  |
| `mcpServers` field exists but is `null` or `{}`                  | Report "no servers declared" — not a failure, just empty                               |

## Examples

**Validate a plugin's `.mcp.json` directly**:

```
/validate-mcp ~/000-projects/claude-code-plugins/plugins/productivity/plane/.mcp.json
```

**Validate inline servers in `plugin.json`**:

```
/validate-mcp ~/000-projects/claude-code-plugins/plugins/integrations/some-plugin/.claude-plugin/plugin.json
```

**Strict-mode audit (plaintext secrets become errors)**:

```
/validate-mcp /path/to/.mcp.json --strict
```

**Discover-then-validate (bare directory argument)**:

```
/validate-mcp /tmp/external-contributor/their-plugin/
```

The skill resolves the canonical location automatically and reports which file it picked.

## Resources

### Canonical specs (saved verbatim in `references/`)

- `references/anthropic-mcp.md` — Anthropic Claude Code MCP integration reference
- `references/mcp-open-spec.md` — open Model Context Protocol spec

### Live canonical URLs

- [code.claude.com/docs/en/mcp](https://code.claude.com/docs/en/mcp) — Claude Code MCP integration
- [modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification) — open MCP protocol
- [code.claude.com/docs/en/plugins-reference#mcp-servers](https://code.claude.com/docs/en/plugins-reference#mcp-servers) — plugin manifest `mcpServers` field

### Related skills

- `/validate-plugin` — orchestrator that delegates here for `.mcp.json` audits
- `/validate-skillmd` — sibling SKILL.md grader (Tier 0/1/2/3)
- `/validate-hook` / `/validate-agent` / `/validate-marketplace` — sibling component validators
