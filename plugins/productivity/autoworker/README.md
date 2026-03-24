# autoworker

Auto-loop execution workflow with quality gates for Claude Code.

## What it does

Enforces a state-machine execution loop: plan → decompose → implement → test (4 layers) → quality gate → iterate until PASS. Claude cannot claim "done" without passing gate-check with evidence.

## Installation

```bash
/plugin marketplace add phj128/autoworker
/plugin install autoworker@autoworker
```

## Skills

| Skill | Role |
|-------|------|
| `autoworker` | Main entry — core rules, execution chain, anti-loss protection |
| `deep-plan` | 5-phase structured planning discussion |
| `subtask-init` | Create subtask with goals, assumptions, acceptance criteria |
| `subtask-plan` | Build L1-L4 verification plan with traceability |
| `dispatch` | State machine router (sole routing point) |
| `code` | Implement one phase |
| `test` | Execute one test layer |
| `checkpoint` | Record progress |
| `gate-check` | Quality gate — confidence assessment, re-work on failure |
| `subtask-update` | Fix steps after gate failure |
| `sync-docs` | Persist and archive |

## Links

- **GitHub**: https://github.com/phj128/autoworker
- **Author**: [@phj128](https://github.com/phj128)
- **License**: MIT
