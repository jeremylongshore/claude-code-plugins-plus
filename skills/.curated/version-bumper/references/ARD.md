# ARD: Version Bumper

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The Version Bumper operates within the claude-code-plugins monorepo to synchronize version numbers across the two-catalog system. It reads and writes JSON files and invokes the marketplace sync script.

```
plugin.json (source version)
       ↓
[Version Bumper]
  ├── Reads: plugin.json, marketplace.extended.json
  ├── Writes: plugin.json, marketplace.extended.json
  └── Calls: jq, pnpm run sync-marketplace, git
       ↓
marketplace.json (auto-regenerated)
```

## Data Flow

1. **Input**: Target plugin path and desired bump type (major/minor/patch) or explicit target version from the user request
2. **Processing**: Read current version with `jq`, compute new version per semver rules, update `plugin.json` and `marketplace.extended.json` in place, run `sync-marketplace` to regenerate `marketplace.json`, then verify all three files match
3. **Output**: Version bump summary showing old-to-new transition, list of updated files, validation confirmation, and suggested git commands (add, commit, tag)

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| `jq` for JSON manipulation | `jq` over Node.js or Python scripts | Zero-dependency, available on all dev machines, precise field updates without reformatting |
| Two-file update + sync | Edit source files, let sync-marketplace regenerate | Follows the repo's two-catalog system: extended.json is source of truth, marketplace.json is derived |
| Post-bump verification | Read all three files and compare versions | Catches sync failures immediately rather than at CI time |
| Optional git operations | Tag and commit suggested but not forced | Some workflows prefer manual git control; others want full automation |
| Semver-only format | Strict `x.y.z` parsing, no pre-release suffixes | Matches the marketplace catalog's version format expectations |
| Plugin name matching | Exact name match in marketplace.extended.json | Prevents accidental updates to similarly-named plugins |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Inspect current versions in plugin.json and marketplace.extended.json |
| Write | Update version fields in both JSON files |
| Edit | Targeted field replacement when Write would reformat the entire file |
| Grep | Find the plugin entry in marketplace.extended.json by name match |
| Bash(cmd:*) | Run `jq` for JSON parsing, `pnpm run sync-marketplace`, and optional `git tag` |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Invalid version format | Version string doesn't match `x.y.z` pattern | Report the current invalid value; prompt user to fix manually before bumping |
| Plugin not in marketplace | Grep for plugin name returns no match in extended.json | Instruct user to add the entry first; provide the required fields |
| Sync failure | `pnpm run sync-marketplace` exits non-zero | Run `jq empty` on both JSON files to locate syntax errors; fix and re-sync |
| Version mismatch after sync | Post-verification shows different versions across files | Re-run the update on the mismatched file; check that plugin names match exactly |
| jq not installed | `command -v jq` returns empty | Provide install command: `apt install jq` or `brew install jq` |

## Extension Points

- Batch bumps: extend to accept a list of plugin paths for coordinated multi-plugin releases
- Changelog integration: auto-generate changelog entries from git log between old and new version tags
- Pre-release versions: support semver pre-release suffixes (e.g., `1.0.0-beta.1`)
- CI hook: run as a post-merge action that auto-bumps patch on every merge to main
- Version history: maintain a version log file tracking all bumps with dates and reasons
- Dependency bumps: cascade version updates to plugins that depend on the bumped plugin
