---
name: hyperfocus
description: >
  ADHD-friendly output formatting. Restructures responses with chunking, visual
  hierarchy, and front-loaded key points. Modes: clean, flow (default), zen.
  Use when user says "hyperfocus", "focus mode", "adhd mode", "adhd friendly",
  or invokes /hyperfocus.
argument-hint: "[clean|flow|zen|off|persistent [project] [mode]|disable|status]"
---

Format responses for ADHD-optimized reading: structure beats brevity. Parse `$ARGUMENTS` against the table below.

## Commands

| Argument | Effect |
|----------|--------|
| *(none)*, `clean`, `flow`, or `zen` | Activate/switch mode for this session only. Default mode: flow |
| `off` | Deactivate hyperfocus for this session |
| `persistent [mode]` | Enable global auto-injection at every future session start (default mode: flow) |
| `persistent project [mode]` | Same, scoped to this project only |
| `disable` | Turn off persistent mode in both global and project state, wherever present |
| `status` | Report session mode plus persistent state |

Plain "stop hyperfocus" or "normal mode" is equivalent to `off`.

## Session activation

On activation or mode switch, read `references/core.md` and `references/<mode>.md` (relative to this skill's directory) and apply their rules to every subsequent response until the user says "stop hyperfocus", "normal mode", or `/hyperfocus off`.

## Persistent, disable, status

Run `scripts/hyperfocus-state`, resolved at `${CLAUDE_PLUGIN_ROOT}/scripts/hyperfocus-state` when installed as a plugin:

- `persistent [mode]` → `hyperfocus-state enable [mode]`
- `persistent project [mode]` → `hyperfocus-state enable [mode] --project`
- `disable` → `hyperfocus-state disable --all`
- `status` → `hyperfocus-state status`

If `${CLAUDE_PLUGIN_ROOT}` is unset (standalone skill install, no plugin root), there is no hook to attach persistence to: tell the user persistent mode isn't available in this install, and apply the requested mode for the current session only.

## Legacy migration (≤0.2)

Check for `~/.claude/hyperfocus-rules.txt` or a `settings.json` hook whose command contains `hyperfocus-rules`. If found, tell the user it's a leftover from hyperfocus ≤0.2 and offer to remove it. Only edit settings.json after the user confirms.

## Boundaries

Code blocks, error messages, technical output, commits, PRs, and code reviews: write normally, without hyperfocus formatting.

## Auto-Clarity

Drop hyperfocus formatting for security warnings and irreversible-action confirmations — use full prose. Numbered steps stay allowed elsewhere; only symbol-substitution and density compression are dropped for safety-critical sequences. Resume formatting after.
