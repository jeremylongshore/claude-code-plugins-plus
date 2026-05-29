---
name: validate-hook
description: |
  Validate a hooks/hooks.json file (or hooks declared in settings.json or
  in skill/agent frontmatter) against the canonical Anthropic hooks reference.
  Checks JSON validity, 3-level event nesting, the ~30-event allowlist
  (PreToolUse, PostToolUse, SessionStart, Stop, SubagentStop, PreCompact,
  UserPromptSubmit, PermissionRequest, Notification, etc. — full list in
  references/anthropic-hooks-reference.md), per-handler required fields by
  type (command, http, mcp_tool, prompt, agent), and matcher regex
  compilability. Bonus: warns when a PreToolUse handler does not document
  its exit-code-2 blocking behavior. Use when reviewing a contributor's
  hooks.json, auditing your own plugin's hooks directory, or spot-checking
  inline hook config in skill or agent frontmatter. Trigger with
  "/validate-hook", "validate this hook", "check hooks.json", "audit hooks
  config", "is this hook spec-correct".
allowed-tools: 'Read,Bash(jq:*),Bash(grep:*),Bash(python3:*),Glob,AskUserQuestion'
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; requires jq + Python 3
tags: [validation, hooks, plugin-quality, claude-code, security]
user-invocable: true
argument-hint: '[path-to-hooks.json | path-to-settings.json] [--strict]'
---

# Validate Hook

Schema validator for Claude Code hook configuration. Reads `hooks/hooks.json` (or hooks declared inline in `settings.json` / skill / agent frontmatter) and grades it against the [canonical Anthropic hooks reference](https://code.claude.com/docs/en/hooks). Anchors every claim in `references/anthropic-hooks-reference.md` so spec drift is detectable and recoverable.

## Overview

Hooks are the most security-sensitive component a plugin can ship. A poorly written `PreToolUse` hook can silently block legitimate work or, worse, allow dangerous tool calls through. This validator enforces the schema rigorously.

**Schema** (3-level nesting per spec):

```json
{
  "hooks": {
    "<EventName>": [
      {
        "matcher": "<pattern>",
        "hooks": [{ "type": "command", "command": "..." }]
      }
    ]
  }
}
```

**Event allowlist** (~30 documented events — exact list in `references/anthropic-hooks-reference.md`):

`PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch`, `SessionStart`, `SessionEnd`, `Stop`, `StopFailure`, `SubagentStart`, `SubagentStop`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `UserPromptExpansion`, `PermissionRequest`, `PermissionDenied`, `Notification`, `TaskCreated`, `TaskCompleted`, `TeammateIdle`, `InstructionsLoaded`, `ConfigChange`, `CwdChanged`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove`, `Elicitation`, `ElicitationResult`, `Setup`.

**Handler types** (each with its own required fields):

| Type       | Required                   | Notes                                                           |
| ---------- | -------------------------- | --------------------------------------------------------------- |
| `command`  | `command`                  | Runs shell command, JSON via stdin, exit code controls behavior |
| `http`     | `url`                      | POSTs to URL, response body is JSON output schema               |
| `mcp_tool` | `server`, `tool`           | Calls MCP server tool with `${path}` substitution               |
| `prompt`   | `prompt`                   | Single-turn LLM evaluation, optional `model` field              |
| `agent`    | `prompt` (or `agent` name) | Spawns subagent                                                 |

## Prerequisites

- `jq` on PATH (every check pipes through `jq`)
- Python 3 (for matcher regex compilability checks via `re.compile`)
- The spec snapshot under `references/anthropic-hooks-reference.md` (symlinked from `validate-plugin/references/`)

## Instructions

### Step 1: Resolve target file

Argument forms:

- **Standalone `hooks.json`** — `/validate-hook /path/to/plugin/hooks/hooks.json`
- **`settings.json`** with hooks block — `/validate-hook /path/to/plugin/settings.json`
- **Bare directory** — `/validate-hook /path/to/plugin/` → look for `hooks/hooks.json`, then `settings.json`
- **Frontmatter (skill/agent)** — extract the `hooks:` YAML block and pass via stdin (rare)

Cache the resolved file as `$HOOKS_FILE` and the JSON path as `$JQ_PATH` (`.hooks` for `hooks.json`, `.hooks` for `settings.json` if present).

### Step 2: JSON validity + structural shape

```bash
HOOKS_FILE="<resolved>"
JQ_PATH=".hooks"

jq empty "$HOOKS_FILE" 2>&1 || { echo "FAIL: malformed JSON"; exit 1; }

# .hooks must be an object
SHAPE=$(jq -r "$JQ_PATH | type" "$HOOKS_FILE")
[ "$SHAPE" = "object" ] || echo "FAIL: $JQ_PATH must be an object, got $SHAPE"
```

### Step 3: Event-name allowlist check

Cross-reference declared event names against the documented allowlist. Build the allowlist inline (matches the exact list in `references/anthropic-hooks-reference.md`):

```bash
ALLOWED_EVENTS="PreToolUse PostToolUse PostToolUseFailure PostToolBatch SessionStart SessionEnd Stop StopFailure SubagentStart SubagentStop PreCompact PostCompact UserPromptSubmit UserPromptExpansion PermissionRequest PermissionDenied Notification TaskCreated TaskCompleted TeammateIdle InstructionsLoaded ConfigChange CwdChanged FileChanged WorktreeCreate WorktreeRemove Elicitation ElicitationResult Setup"

jq -r "$JQ_PATH | keys[]" "$HOOKS_FILE" | while read -r evt; do
  if ! echo " $ALLOWED_EVENTS " | grep -q " $evt "; then
    echo "FAIL: unknown event name '$evt' (not in canonical allowlist)"
  fi
done
```

### Step 4: Per-event matcher + handler shape

Each event maps to an array of `{matcher, hooks}` entries. `matcher` is optional (or `"*"` for match-all) and must be a regex string when present. `hooks` must be an array of handler objects.

```bash
jq -r "$JQ_PATH | to_entries[] |
  .key as \$evt |
  .value | to_entries[] |
  \"\\(\$evt)|\\(.key)|\\(.value.matcher // \\\"\\\")|\\(.value.hooks | type)|\\(.value.hooks | length // 0)\"
" "$HOOKS_FILE" | while IFS='|' read -r evt idx matcher hooks_type hooks_len; do
  [ "$hooks_type" = "array" ] || echo "FAIL $evt[$idx]: 'hooks' must be an array, got $hooks_type"
  [ "$hooks_len" -gt 0 ] || echo "WARN $evt[$idx]: 'hooks' array is empty"
done
```

### Step 5: Per-handler required-field check

For each handler, validate the type and its required fields:

```bash
jq -r "
  $JQ_PATH | to_entries[] |
  .key as \$evt |
  .value[] |
  .hooks[] |
  \"\\(\$evt)|\\(.type // \\\"command\\\")|\\(.command // \\\"\\\")|\\(.url // \\\"\\\")|\\(.server // \\\"\\\")|\\(.tool // \\\"\\\")|\\(.prompt // \\\"\\\")\"
" "$HOOKS_FILE" | while IFS='|' read -r evt type command url server tool prompt; do
  case "$type" in
    command)
      [ -n "$command" ] || echo "FAIL $evt: command-type handler requires 'command' field"
      ;;
    http)
      [ -n "$url" ] || echo "FAIL $evt: http-type handler requires 'url' field"
      ;;
    mcp_tool)
      [ -n "$server" ] && [ -n "$tool" ] || echo "FAIL $evt: mcp_tool-type handler requires 'server' + 'tool' fields"
      ;;
    prompt|agent)
      [ -n "$prompt" ] || echo "FAIL $evt: $type-type handler requires 'prompt' field"
      ;;
    *)
      echo "FAIL $evt: unknown handler type '$type' (allowed: command, http, mcp_tool, prompt, agent)"
      ;;
  esac
done
```

### Step 6: Matcher regex compilability

A matcher regex that fails to compile silently disables the hook. Verify each one parses:

```bash
jq -r "
  $JQ_PATH | to_entries[] |
  .value[] |
  select(.matcher != null and .matcher != \"\" and .matcher != \"*\") |
  .matcher
" "$HOOKS_FILE" | while read -r pattern; do
  python3 -c "import re,sys; re.compile(sys.argv[1])" "$pattern" 2>&1 \
    || echo "FAIL: matcher regex '$pattern' fails to compile"
done
```

### Step 7: Bonus — `PreToolUse` exit-code-2 documentation check

`PreToolUse` is the only hook event that can BLOCK a tool call (via exit code 2). Authors who don't document the blocking behavior in their hook script tend to ship surprising plugins. Warn when the script's first 20 lines have no comment mentioning exit code 2 or "block":

```bash
jq -r "
  $JQ_PATH | to_entries[] |
  select(.key == \"PreToolUse\") |
  .value[] |
  .hooks[] |
  select(.type == \"command\") |
  .command
" "$HOOKS_FILE" | while read -r cmd; do
  # Resolve script path (first token)
  SCRIPT=$(echo "$cmd" | awk '{print $1}')
  if [ -f "$SCRIPT" ]; then
    head -20 "$SCRIPT" | grep -qiE "exit.*2|block|prevent" \
      || echo "WARN PreToolUse handler '$SCRIPT' does not document its exit-code-2 blocking behavior"
  fi
done
```

In `--strict` mode, promote this warning to an error.

### Step 8: Verdict

- **PASS** — JSON valid, all events in allowlist, every handler has its type-required field, all matchers compile
- **WARN** — empty `hooks` arrays, undocumented `PreToolUse` blocking
- **FAIL** — malformed JSON, unknown event name, unknown handler type, missing type-required field, matcher regex fails to compile

## Output

```
══════════════════════════════════════════════════════════════════════
  HOOKS CONFIG AUDIT — <file-path>
══════════════════════════════════════════════════════════════════════

  JSON validity:                              PASS
  Top-level shape (.hooks):                   object (PASS)
  Events declared:                            <list>

  Event-name allowlist:
    <event>:                                  PASS / FAIL — not in allowlist

  Per-handler verdicts:
    <event>[0]  type=command                  PASS
    <event>[1]  type=http                     FAIL — missing 'url'
    <event>[2]  type=mcp_tool                 PASS

  Matcher regex compilability:                <N> ok / <M> failed
    Failed: '<pattern>'                       <python re error>

  Security:
    PreToolUse handler '<script>'             WARN — no exit-code-2 docs

  ──────────────────────────────────────────────────────────────────
  VERDICT: PASS | FAIL — <count> blocking issue(s)
  ──────────────────────────────────────────────────────────────────
```

## Error Handling

| Error                                                            | Recovery                                                                        |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Target file not found                                            | Use `Glob` to search for `hooks/hooks.json`; ask for clarification              |
| Both `hooks/hooks.json` and inline `settings.json` hooks present | Use AskUserQuestion to pick which to validate                                   |
| JSON parse error                                                 | Surface jq parse error verbatim with line number                                |
| Unknown event name                                               | Cite `references/anthropic-hooks-reference.md` allowlist; suggest closest match |
| Unknown handler type                                             | Cite documented types (command/http/mcp_tool/prompt/agent)                      |
| Matcher regex fails to compile                                   | Surface Python `re.error` verbatim                                              |
| `PreToolUse` script not on disk                                  | Skip exit-code-2 doc check silently                                             |
| `--strict` mode                                                  | Promote all WARN findings to FAIL                                               |

## Examples

**Validate a plugin's hooks.json**:

```
/validate-hook ~/000-projects/claude-code-plugins/plugins/devops/some-plugin/hooks/hooks.json
```

**Validate hooks declared in settings.json**:

```
/validate-hook /path/to/plugin/settings.json
```

**Strict-mode audit (security warnings become errors)**:

```
/validate-hook /path/to/hooks.json --strict
```

**Discover-then-validate (bare directory argument)**:

```
/validate-hook /tmp/external-contributor/their-plugin/
```

The skill resolves the canonical hooks location automatically.

## Resources

### Canonical spec (saved verbatim in `references/`)

- `references/anthropic-hooks-reference.md` — full hooks reference (events, handler types, exit codes, JSON output format, frontmatter form)

### Live canonical URLs

- [code.claude.com/docs/en/hooks](https://code.claude.com/docs/en/hooks) — hooks reference
- [code.claude.com/docs/en/plugins-reference#hooks](https://code.claude.com/docs/en/plugins-reference#hooks) — hooks in the plugin manifest

### Related skills

- `/validate-plugin` — orchestrator that delegates here for hooks.json audits
- `/validate-skillmd` — sibling SKILL.md grader (frontmatter `hooks:` field validates here too)
- `/validate-mcp` / `/validate-agent` / `/validate-marketplace` — sibling component validators
