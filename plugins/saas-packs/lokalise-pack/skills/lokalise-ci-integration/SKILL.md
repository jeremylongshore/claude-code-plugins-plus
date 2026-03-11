---
name: lokalise-ci-integration
description: |
  Configure Lokalise CI/CD integration with GitHub Actions and automated sync.
  Use when setting up automated translation sync, configuring CI pipelines,
  or integrating Lokalise into your build process.
  Trigger with phrases like "lokalise CI", "lokalise GitHub Actions",
  "lokalise automated sync", "CI lokalise", "lokalise pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise CI Integration

## Overview
Automate translation workflows with Lokalise in CI/CD pipelines. Covers pushing source strings on merge, pulling translations before builds, validating translation completeness, and webhook-triggered deployments.

## Prerequisites
- Lokalise API token stored as GitHub secret
- Lokalise CLI (`@lokalise/cli2`) or API SDK
- GitHub Actions configured
- Project ID identified

## Instructions

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Upload fails | Invalid JSON | Validate locale files before push |
| Missing translations | Download with empty strings | Use `--export-empty-as skip` |
| Webhook not triggered | Dispatcher not configured | Set up Lokalise webhook to GitHub |
| Wrong file structure | Prefix mismatch | Use `--directory-prefix ""` in download |

## Examples
### Local Translation Script
```bash
#!/bin/bash
# scripts/lokalise-pull.sh
lokalise2 file download \
  --token "$LOKALISE_API_TOKEN" \
  --project-id "$LOKALISE_PROJECT_ID" \
  --format json \
  --unzip-to "src/locales/"
echo "Translations updated"
```

## Resources
- [Lokalise CLI Reference](https://docs.lokalise.com/cli2)
- [Lokalise GitHub Actions](https://docs.lokalise.com/integrations/github)
- [Lokalise Webhooks](https://docs.lokalise.com/webhooks)
