---
name: lokalise-local-dev-loop
description: |
  Configure Lokalise local development with file sync and hot reload.
  Use when setting up a development environment, configuring translation sync,
  or establishing a fast iteration cycle with Lokalise.
  Trigger with phrases like "lokalise dev setup", "lokalise local development",
  "lokalise dev environment", "develop with lokalise", "lokalise sync".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Bash(lokalise2:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise Local Dev Loop

## Overview
Set up a fast, reproducible local development workflow for Lokalise with automatic translation sync.

## Prerequisites
- Completed `lokalise-install-auth` setup
- Node.js 18+ with npm/pnpm
- Lokalise CLI v2 (`lokalise2`) installed
- Existing Lokalise project

## Instructions

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Working development environment with translation sync
- CLI scripts for push/pull operations
- Optional file watcher for automatic uploads
- Pre-build hooks ensure translations are current

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `project_id not found` | Missing config | Set LOKALISE_PROJECT_ID or lokalise.json |
| `File not found` | Wrong path | Check bundle_structure matches src/locales |
| `Rate limit 429` | Too many requests | Add delay between operations |
| `Polling timeout` | Large file upload | Increase poll-timeout |

## Examples
### Quick Pull/Push Commands
```bash
# Pull all translations
npm run i18n:pull

# Push source strings only
npm run i18n:push

# Full sync (push then pull)
npm run i18n:sync
```

### Environment Setup
```bash
# .env.local
LOKALISE_API_TOKEN=your-api-token
LOKALISE_PROJECT_ID=123456789.abcdef
```

## Resources
- [Lokalise CLI Documentation](https://docs.lokalise.com/en/articles/3401683-lokalise-cli-v2)
- [File Upload API](https://developers.lokalise.com/reference/upload-a-file)
- [File Download API](https://developers.lokalise.com/reference/download-files)

## Next Steps
See `lokalise-sdk-patterns` for production-ready code patterns.
