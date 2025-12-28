---
name: changelog-validate
description: Validate changelog config, tokens, and template paths
category: documentation
---

# /changelog-validate

Validate `.changelog-config.json` before generating a changelog.

## Checks

- Config exists and is valid JSON
- Required environment variables exist (e.g., `GITHUB_TOKEN`, optional `SLACK_TOKEN`)
- Template path exists
- Output path is writable

If validation fails, show actionable fixes (missing token env vars, missing template, invalid paths).

