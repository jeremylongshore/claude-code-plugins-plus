<!-- doc-class: record -->

# Release Report: claude-code-plugins v4.14.0

## Executive Summary

- **Version**: 4.14.0
- **Release Date**: 2026-01-31
- **Release Type**: MINOR
- **Approved By**: jeremy
- **Duration**: ~10 minutes

## Pre-Release State

### Pull Requests

- Open PRs: 0
- Merged before release: 0
- Deferred: 0

### Branch State

- Working directory: Clean
- All commits pushed: Yes
- Stashes: 0

### Security

- Secrets scan: PASS
- No tracked .env files
- License: MIT

## Changes Included

### Features

- 17 additional SaaS skill packs (408 skills)
- Complete SaaS pack collection: 42 packs with 1,086 skills
- Website updates with accurate pack counts and cards

### New SaaS Packs

apollo, clerk, coderabbit, customerio, deepgram, fireflies, gamma, granola,
groq, ideogram, instantly, juicebox, langchain, linear, lindy, posthog, vastai

### Breaking Changes

- None

## Documentation Updates

### README Changes

- Version badge: 4.13.0 → 4.14.0
- Skills count: 739 → 1,537
- SaaS pack description updated

### CHANGELOG

- Added v4.14.0 entry with full pack details

### Website

- Updated hero section with correct counts
- Added 3 new pack cards (Groq, LangChain, PostHog)
- Changed placeholder to link to browse all packs

## Metrics

| Metric                  | Value   |
| ----------------------- | ------- |
| Commits since v4.13.0   | 3       |
| Files Changed           | 16      |
| Lines Added             | +31,928 |
| Lines Removed           | -13,757 |
| Contributors            | 1       |
| Days Since Last Release | 5       |

### Skill Metrics

| Metric       | v4.13.0 | v4.14.0 | Change |
| ------------ | ------- | ------- | ------ |
| SaaS Packs   | 25      | 42      | +17    |
| SaaS Skills  | 678     | 1,086   | +408   |
| Total Skills | 1,027   | 1,537   | +510   |

## Quality Gates

| Gate                | Status   |
| ------------------- | -------- |
| Quick Tests         | ✓ Passed |
| Build               | ✓ Passed |
| Lint                | ✓ Passed |
| Plugin Validation   | ✓ Passed |
| Secrets Scan        | ✓ Passed |
| Version Consistency | ✓ Passed |

## Rollback Procedure

If issues discovered:

```bash
# Remove release
git push origin --delete v4.14.0
git tag -d v4.14.0
gh release delete v4.14.0 --yes

# Revert changes
git revert HEAD~2..HEAD
git push origin main
```

## Post-Release Checklist

- [x] Tag created and pushed
- [x] GitHub release published
- [x] Version files updated
- [ ] Monitor error rates for 24h
- [ ] Check user feedback channels

## Release URL

https://github.com/jeremylongshore/claude-code-plugins-plus-skills/releases/tag/v4.14.0

---

Generated: 2026-01-31T22:53:00Z
