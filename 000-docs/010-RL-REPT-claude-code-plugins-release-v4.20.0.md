<!-- doc-class: record -->

# Release Report: claude-code-plugins v4.20.0

## Executive Summary

- **Version**: 4.20.0
- **Release Date**: 2026-03-20
- **Release Type**: Minor
- **Approved By**: jeremy
- **Duration**: ~25 minutes

## Pre-Release State

### Pull Requests

- Merged before release: PR #372 (pr-to-spec MCP plugin + 8 SaaS pack rewrites)
- Deferred: 0
- Blocked: 0

### Branch State

- Branches merged: feat/pr-to-spec-mcp (squash merged)
- Branches cleaned: 1 (deleted after merge)

### Security

- Vulnerabilities addressed: 0
- Secrets scan: PASS
- Dependency audit: PASS
- CodeQL: PASS

## Changes Included

### Features

- pr-to-spec MCP plugin (6 tools for agentic PR workflows)
- claude-memory-kit plugin (@seankim-android)
- prism-scanner plugin (@aidongise-cell)
- Content consistency validator improvements (@fernandezbaptiste)

### SaaS Pack Rewrites (150+ skills)

- MaintainX pack (24 skills) - CMMS API integration
- Evernote pack (24 skills) - Note management workflows
- Apollo pack (22 skills) - Sales engagement APIs
- Clerk pack (22 skills) - Auth/user management
- Speak pack (9 skills) - Language learning APIs
- Obsidian pack (10 skills) - Vault plugin development
- Lokalise pack (23 skills) - Localization workflows
- Juicebox pack (18 skills) - Community platform APIs

### Fixes

- Homepage badge redundancy
- HTML attribute sanitization (CodeQL)
- Repository URL consistency (pr-to-spec -> pr-to-prompt)
- Validation script duplicate tuple

### Breaking Changes

- None

## Documentation Updates

### CHANGELOG

- Entries added: 4 sections (Added, Changed, Fixed, Metrics)
- Format: Keep a Changelog 1.0.0

### README Changes

- No changes required

## Metrics

| Metric                  | Value   |
| ----------------------- | ------- |
| Commits                 | 13      |
| Files Changed           | 432     |
| Lines Added             | +56,454 |
| Contributors            | 5       |
| Days Since Last Release | 3       |

## External Artifacts

| Artifact       | Status  | Details                                                                                 |
| -------------- | ------- | --------------------------------------------------------------------------------------- |
| GitHub Release | CREATED | https://github.com/jeremylongshore/claude-code-plugins-plus-skills/releases/tag/v4.20.0 |
| GitHub Gist    | STALE   | https://gist.github.com/a61dcd78f4a28bc32bed07997d9de3fb (needs manual update)          |

## Quality Gates

| Gate                   | Status          |
| ---------------------- | --------------- |
| Tests Passing          | PASS            |
| Secrets Scan           | PASS            |
| Dependency Audit       | PASS            |
| Branch Protection      | PASS (restored) |
| Documentation Current  | PASS            |
| CodeQL                 | PASS            |
| Marketplace Validation | PASS            |
| Playwright Tests       | PASS            |

## CI Notes

- production-e2e: FAIL (known flaky - GitHub avatar CDN rate limits)
- All other checks: PASS

## Rollback Procedure

If issues discovered:

```bash
# Remove release
git push origin --delete v4.20.0
git tag -d v4.20.0
gh release delete v4.20.0 --yes

# Revert changes
git revert HEAD
git push origin main
```

## Post-Release Checklist

- [x] Tag created and pushed
- [x] GitHub release created
- [x] Branch protection restored
- [ ] Monitor error rates for 24h
- [ ] Update project board/roadmap
- [ ] Gist update (deferred)

---

_Generated: 2026-03-20T05:43:00Z_
_Release Automation: Claude Code /release skill_
