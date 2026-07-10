---
name: hyperflow-audit
description: Hyperflow code review. Use when the user wants the current diff, a commit, branch, or PR reviewed — verbs like audit, review, "check for issues", "security check", "code review". Multi-level review (L1 quick → L5 exhaustive), writes findings to .hyperflow/audits/, then a fix-gate.
---

# hyperflow-audit — review phase (Antigravity single-agent)

Multi-level review over a target (default: `git diff HEAD` + staged). Follow the `hyperflow` doctrine. Security scan is mandatory at L3+.

## Levels

| L | Checks |
|---|--------|
| 1 | syntax, obvious bugs, formatting |
| 2 | L1 + spec compliance, naming, edge cases |
| 3 | L2 + cross-file consistency, integration risks, security (secrets, injection, path traversal, XSS, missing validation) |
| 4 | L3 + architecture, scalability, accessibility |
| 5 | L4 + adversarial probing, perf profiling, alternatives |

Default to L2; elevate to L3 when the diff touches auth, data, money, or external input.

## Steps

1. **Resolve scope** (target arg or current diff). Read the changed files + their immediate dependencies.
2. **Review** at the chosen level. Grade each finding `[Critical] / [Important] / [Suggestion] / [Praise]` with `file:line` + a concrete fix.
3. **Write** the full report to `.hyperflow/audits/<YYYY-MM-DD-HHmm>-<scope>.md` (status table → TL;DR → findings → security-scan table). Print a one-line summary pointing at the file.
4. **Fix gate** via AskUserQuestion (only when Critical/Important exist): `Fix all (Recommended) / Critical+Important / Critical only / No`. On a fix choice, route the findings into `hyperflow-plan` → `hyperflow-dispatch`. On `SECURITY_VIOLATION`, skip the gate and surface immediately.

## Rules

- Findings live in the file, not chat — chat shows only the summary box.
- A clean run (no Critical/Important) prints `Audit clean` and still writes the file for history.
