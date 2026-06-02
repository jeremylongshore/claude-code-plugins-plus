---
name: hyperflow-sticky
description: Hyperflow auto-routing mode. Use to control how aggressively hyperflow auto-routes — "make hyperflow sticky", "stop using hyperflow", "auto-route to hyperflow", "disable hyperflow auto-routing". Sets on (every task-shaped message routes) / auto (intent-verb messages route — default) / off (no auto-routing).
---

# hyperflow-sticky — auto-routing mode (Antigravity single-agent)

Control hyperflow's auto-routing aggressiveness. Follow the `hyperflow` doctrine.

## Modes

- **on** — every task-shaped message routes through a hyperflow workflow.
- **auto** (default) — only messages whose first verb matches the routing table (build/fix/audit/scope/design/ship…) route.
- **off** — no auto-routing; hyperflow runs only when a `/hyperflow*` command is explicitly invoked.

## Steps

1. Read the requested mode (on / auto / off).
2. Write it to `.hyperflow/.sticky-mode` (one word).
3. The core `hyperflow` skill reads this on each task to decide whether to auto-route.
4. Print the new mode.

## Rules

- This only changes routing behavior — it never runs work. Default is `auto` when the file is absent.
