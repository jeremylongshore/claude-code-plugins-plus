---
name: pr-to-spec
description: Analyze code changes and detect intent drift using pr-to-spec CLI
version: 0.8.0
author: Jeremy Longshore
triggers:
  - /pr-to-spec
  - pr-to-spec scan
  - pr-to-spec check
  - pr-to-spec intent
---

# pr-to-spec Skill

Convert code changes into structured, agent-consumable specs with intent drift detection.

## Commands

### /pr-to-spec scan
Analyze current branch changes vs main and output a structured spec.

```bash
pr-to-spec scan --branch main --json
```

Use `--diff N` to scan last N commits, or `--staged` for staged changes only.

### /pr-to-spec check
Scan current changes AND check for drift against declared intent.

```bash
pr-to-spec check --json
```

Returns exit code 3 if drift is detected, 2 if high-risk, 0 if clean.

### /pr-to-spec intent set
Declare what this change is supposed to do.

```bash
pr-to-spec intent set --goal "Add rate limiting to API" --scope "src/middleware/**" --forbid "src/db/**" --max-risk medium
```

### /pr-to-spec intent show
Show the current intent declaration.

```bash
pr-to-spec intent show --json
```

## Agent Protocol

All `--json` output is wrapped in the agent protocol envelope:

```json
{
  "version": 1,
  "command": "check",
  "status": "drift_detected",
  "exit_code": 3,
  "signals": [...],
  "spec": {...},
  "intent": {...}
}
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Clean — no issues |
| 1 | Error |
| 2 | High-risk changes detected |
| 3 | Drift detected |

## Usage in CLAUDE.md

Add to your project's CLAUDE.md:

```markdown
## Change Validation

Before any significant code change:
1. Set intent: `pr-to-spec intent set --goal "..." --scope "..." --max-risk medium`
2. After changes: `pr-to-spec check --json` — exit 3 means drift, investigate before continuing
```
