---
name: lokalise-hello-world
description: |
  Create a minimal working Lokalise example.
  Use when starting a new Lokalise integration, testing your setup,
  or learning basic Lokalise API patterns.
  Trigger with phrases like "lokalise hello world", "lokalise example",
  "lokalise quick start", "simple lokalise code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lokalise Hello World

## Overview
Minimal working example demonstrating core Lokalise functionality: projects, keys, and translations.

## Prerequisites
- Completed `lokalise-install-auth` setup
- Valid API token configured
- At least one Lokalise project (or we'll create one)

## Instructions

1. For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Working TypeScript/JavaScript file with Lokalise client
- Successfully listed, created projects
- Added translation keys with multiple languages
- Retrieved translations

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid token | Check LOKALISE_API_TOKEN |
| `400 Bad Request` | Invalid project/key params | Verify required fields |
| `404 Not Found` | Project doesn't exist | Check project_id |
| `429 Too Many Requests` | Rate limit hit | Wait 1 second, retry |

## Examples
### Using CLI for Quick Test
```bash
# List projects
lokalise2 --token $LOKALISE_API_TOKEN project list

# Get project details
lokalise2 --token $LOKALISE_API_TOKEN project --project-id YOUR_PROJECT_ID

# List keys in a project
lokalise2 --token $LOKALISE_API_TOKEN key list --project-id YOUR_PROJECT_ID
```

## Resources
- [Lokalise API Reference](https://developers.lokalise.com/reference/lokalise-rest-api)
- [Projects API](https://developers.lokalise.com/reference/list-all-projects)
- [Keys API](https://developers.lokalise.com/reference/list-all-keys)
- [Translations API](https://developers.lokalise.com/reference/list-all-translations)

## Next Steps
Proceed to `lokalise-local-dev-loop` for development workflow setup.