# PRD: Version Bumper

**Version:** 1.0.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Claude Code plugins store version numbers in multiple locations (`plugin.json`, `marketplace.extended.json`, and the auto-generated `marketplace.json`). Manual version bumps lead to inconsistencies: one file updated but another forgotten, marketplace out of sync, and CI failures from version mismatches. Developers need a single command that applies semver bumps atomically across all version-bearing files and regenerates the marketplace catalog.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| Plugin Author | Releasing a new version after feature work or bugfixes | Atomic semver bump across all files with marketplace sync |
| Maintainer | Batch-releasing multiple plugins in a coordinated update | Consistent version bumps with git tag creation and commit message |
| CI Pipeline | Automated release triggered by merge to main | Programmatic version update that passes validation without manual intervention |

## Success Criteria

1. Version updated consistently across `plugin.json`, `marketplace.extended.json`, and regenerated `marketplace.json` in a single operation
2. Post-bump validation confirms all three files carry the identical version string
3. Correct semver increment applied: patch for fixes, minor for features, major for breaking changes
4. Optional git tag and commit created following the `chore: Release v<version>` convention

## Functional Requirements

1. Read current version from `.claude-plugin/plugin.json` using `jq -r '.version'`
2. Determine bump type (major/minor/patch) from user request or infer from change context
3. Parse the version into `major.minor.patch` components and compute the new version per semver rules
4. Update the version field in `.claude-plugin/plugin.json`
5. Locate and update the matching entry in `.claude-plugin/marketplace.extended.json`
6. Run `pnpm run sync-marketplace` to regenerate `marketplace.json`
7. Verify version consistency across all three files
8. Optionally create a git tag and prepare a commit message

## Non-Functional Requirements

- Bump operation must be idempotent: running twice with the same target version produces no additional changes
- Must work on any plugin in the repository regardless of category or type
- JSON formatting must be preserved (no whitespace changes beyond the version field)
- Version strings must strictly follow semantic versioning (`major.minor.patch`)
- Sync-marketplace must complete without errors after version update
- Git operations (tag, commit) are optional and never executed without user acknowledgment

## Dependencies

- `jq` installed and available on PATH
- Read/write access to `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.extended.json`
- `pnpm run sync-marketplace` available at the repository root
- Git installed for optional tag creation

## Out of Scope

- Changelog generation (handled by separate tooling)
- Publishing to npm or other package registries
- Updating version references inside SKILL.md frontmatter (those track independently)
- Multi-plugin batch bumps in a single invocation
- Pre-release version suffixes (e.g., `1.0.0-beta.1`)
- Rollback to a previous version
