---
name: lokalise-upgrade-migration
description: |
  Analyze, plan, and execute Lokalise SDK upgrades with breaking change detection.
  Use when upgrading Lokalise SDK versions, detecting deprecations,
  or migrating to new API versions.
  Trigger with phrases like "upgrade lokalise", "lokalise migration",
  "lokalise breaking changes", "update lokalise SDK", "analyze lokalise version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lokalise Upgrade Migration

## Overview
Guide for upgrading Lokalise SDK versions and handling breaking changes.

## Prerequisites
- Current Lokalise SDK installed
- Git for version control
- Test suite available
- Staging environment

## Instructions

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Updated SDK version
- Fixed breaking changes
- Passing test suite
- Documented rollback procedure

## Error Handling
| SDK Version | Node.js | Key Changes |
|-------------|---------|-------------|
| 9.x | 18+ | Pure ESM, no require() |
| 8.x | 14+ | Last CommonJS support |
| 7.x | 14+ | Cursor pagination |
| 6.x | 12+ | TypeScript improvements |

## Examples
### Rollback Procedure
```bash
# If upgrade causes issues, rollback immediately
npm install @lokalise/node-api@8.x.x --save-exact

# Revert ESM changes if needed
git checkout HEAD~1 -- tsconfig.json package.json

# Verify rollback
npm test
```

### CLI Upgrade
```bash
# macOS
brew upgrade lokalise2

# Linux - download latest release
curl -sL https://github.com/lokalise/lokalise-cli-2-go/releases/latest/download/lokalise2_linux_x86_64.tar.gz | tar xz

# Verify
lokalise2 --version
```

## Resources
- [Node SDK Changelog](https://lokalise.github.io/node-lokalise-api/additional_info/changelog.html)
- [API Changelog](https://developers.lokalise.com/docs/api-changelog)
- [CLI Releases](https://github.com/lokalise/lokalise-cli-2-go/releases)

## Next Steps
For CI integration during upgrades, see `lokalise-ci-integration`.
