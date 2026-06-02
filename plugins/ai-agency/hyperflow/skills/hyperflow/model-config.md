# Model Configuration

Multi-provider model selection with per-role overrides and runtime switching.

## Config File

Location: `~/.hyperflow/config.json` (global, all projects).

### Minimal config

```json
{
  "defaults": {
    "thinking": "opus-4-8",
    "worker": "sonnet-4-6"
  }
}
```

### Full config

```json
{
  "activeProvider": null,
  "defaults": {
    "thinking": "opus-4-8",
    "worker": "sonnet-4-6"
  },
  "providers": {
    "claude-code": {
      "thinking": "opus-4-8",
      "worker": "sonnet-4-6",
      "roles": {
        "reviewer": "opus-4-7",
        "searcher": "haiku-4-5"
      }
    },
    "codex": {
      "thinking": "gpt-5.5",
      "worker": "gpt-5.4",
      "reasoning": {
        "thinking": "adaptive",
        "worker": "low"
      }
    },
    "antigravity": {
      "thinking": "gemini-3-pro",
      "worker": "gemini-3.5-flash"
    }
  }
}
```

## Provider Auto-Detection

Detection runs at session start. First match wins:

| Priority | Check | Provider |
|---|---|---|
| 1 | `HYPERFLOW_PROVIDER` env var | Value of env var |
| 2 | `activeProvider` in config.json | Config value |
| 3 | `CLAUDE_CODE_*` env vars present | `claude-code` |
| 4 | `OPENCODE_*` env vars or `opencode` in PATH | `opencode` |
| 5 | `CODEX_*` env vars or `codex` in PATH | `codex` |
| 6 | `ANTIGRAVITY_*` env vars or `antigravity` in PATH | `antigravity` |
| 7 | None matched | Use `defaults` directly |

## Model Resolution

For any role, resolve the model using this priority chain (highest first):

1. **Per-task inline request** — user says "use opus-4-8 for this"
2. **Session override** — `hyperflow: thinking opus-4-8` command
3. **Env var** — `HYPERFLOW_THINKING_MODEL` or `HYPERFLOW_WORKER_MODEL`
4. **Role override** — `providers.<detected>.roles.<role>`
5. **Provider tier** — `providers.<detected>.thinking` or `.worker`
6. **Global default** — `defaults.thinking` or `.worker`

### Role-to-Tier Mapping

| Role | Tier | Description |
|---|---|---|
| `orchestrator` | thinking | Decomposes tasks, coordinates workers |
| `reviewer` | thinking | Reviews every worker output |
| `debugger` | thinking | Root cause analysis |
| `decision-maker` | thinking | Architecture, approach selection |
| `brainstormer` | thinking | Design exploration, proposals |
| `implementer` | worker | Writes code, edits files |
| `searcher` | worker | Explores codebase, finds files |
| `writer` | worker | Tests, docs, configs |

## Codex Reasoning

Codex defaults to `gpt-5.5` for thinking roles and `gpt-5.4` for worker roles. Thinking reasoning is adaptive by task/profile:

| Work type | Reasoning |
|---|---|
| Trivial docs/config checks | `low` |
| Normal implementation planning/review | `medium` |
| Debugging, architecture, security, final integration review | `high` |

Worker fast mode is fixed at `low` unless the user overrides it. Codex defaults never use `xhigh`.

## Claude Code Model Mapping

The Agent tool's `model` parameter accepts aliases, not full model IDs. Map config values:

| Config Value | `model:` param | Version Pinning Env Var |
|---|---|---|
| `opus-4-8` | `"opus"` | None needed (current default) |
| `opus-4-7` | `"opus"` | `ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-4-7` |
| `opus-4-6` | `"opus"` | `ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-4-6` |
| `opus-4-5` | `"opus"` | `ANTHROPIC_DEFAULT_OPUS_MODEL=claude-opus-4-5` |
| `sonnet-4-6` | `"sonnet"` | None needed (current default) |
| `sonnet-4-5` | `"sonnet"` | `ANTHROPIC_DEFAULT_SONNET_MODEL=claude-sonnet-4-5` |
| `haiku-4-5` | `"haiku"` | None needed (current default) |

## Hybrid Model List Detection

When presenting the model picker during install:

1. **Claude Code:** Read `~/.claude/settings.json` to detect current model. Supplement hardcoded list.
2. **OpenCode:** Run `opencode models list --json` (2s timeout). Merge with hardcoded list.
3. **Codex:** Detect `CODEX_*` and the `codex` binary. Use `gpt-5.5` / `gpt-5.4` defaults unless overridden.
4. **Antigravity:** Read `~/.gemini/antigravity/settings.json`. Merge with hardcoded list.

Dynamic models supplement the hardcoded list (don't replace). Fall back to hardcoded if fetch fails.

## Runtime Commands

| Command | Effect | Scope |
|---|---|---|
| `hyperflow: thinking <model>` | Switch thinking model | Current session |
| `hyperflow: worker <model>` | Switch worker model | Current session |
| `hyperflow: models` | Show current model config | Display only |
| `hyperflow: reset models` | Revert to config.json defaults | Current session |

## Environment Variables

| Variable | Purpose |
|---|---|
| `HYPERFLOW_PROVIDER` | Force provider (skip auto-detect) |
| `HYPERFLOW_THINKING_MODEL` | Override thinking model for this session |
| `HYPERFLOW_WORKER_MODEL` | Override worker model for this session |

Also relevant for Claude Code version pinning:
| Variable | Purpose |
|---|---|
| `ANTHROPIC_DEFAULT_OPUS_MODEL` | Pin what `model: "opus"` resolves to |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | Pin what `model: "sonnet"` resolves to |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | Pin what `model: "haiku"` resolves to |
| `CLAUDE_CODE_SUBAGENT_MODEL` | Override model for all subagents |
