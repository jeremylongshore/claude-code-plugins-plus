---
name: changelog-custom
description: Generate a changelog draft for a custom date range
category: documentation
---

# /changelog-custom

Generate a changelog for a custom date range and prepare a branch/PR.

## Parameters

- `start_date=YYYY-MM-DD` (required)
- `end_date=YYYY-MM-DD` (required)

## Steps

1. Ensure `.changelog-config.json` exists at repo root (copy `${CLAUDE_PLUGIN_ROOT}/config/changelog-config.example.json` if missing).
2. Validate setup by running `/changelog-validate` first.
3. Use the `changelog-orchestrator` skill to run the workflow for the provided date range.

