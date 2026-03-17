# Box Cloud Filesystem

Transparent cloud filesystem for AI agents using the official [Box](https://www.box.com/) CLI (`@box/cli`). Upload, download, search, share, and sync files to Box cloud storage with operational safety guardrails. Works with any Box account — personal, business, or enterprise.

**Compatible with:** Claude Code, Codex, Perplexity Computer, OpenClaw, and any agent platform that supports skills or system prompts.

## Why

Box CLI gives agents raw access to cloud storage. Raw access is not the same as useful access. Without guidance, agents guess at folder targets, create duplicates instead of versioning, default to public sharing, and have no sync pattern.

This plugin adds two layers:

1. **Hooks (transparent sync)** — PostToolUse hooks on Write/Edit auto-upload changed files to Box. The agent just writes files normally.
2. **SKILL.md (operator's manual)** — teaches agents explicit Box operations with safety guardrails: trust zones, version-first updates, narrow sharing defaults, conflict detection.

## Install

### From Tons of Skills Marketplace

```bash
ccpi install box-cloud-filesystem
```

### Standalone (from GitHub)

```bash
git clone https://github.com/jeremylongshore/box-cloud-filesystem.git
```

Then symlink or copy into your Claude Code plugins directory, or reference it directly in your agent configuration.

### Prerequisites

```bash
npm install --global @box/cli
box login
box users:get --me   # verify auth
```

`jq` is required for the hook scripts. Install via your system package manager if not present.

Box offers a free tier for individual users. See [box.com](https://www.box.com/) for current pricing and storage limits.

## What's Inside

| Component | Path | Purpose |
|-----------|------|---------|
| Skill | `skills/box-cloud-filesystem/SKILL.md` | Comprehensive Box CLI guide with safety guardrails |
| Hooks | `hooks/hooks.json` | PostToolUse (Write/Edit → Box upload) + Stop (sync summary) |
| Init script | `scripts/box-init-workspace.sh` | Pull Box folder locally + build manifest |
| Sync script | `scripts/box-sync-on-write.sh` | Hook handler: upload changed files to Box |
| Summary script | `scripts/box-sync-summary.sh` | Stop hook: report what was synced |

## Quick Start

**Transparent mode** — initialize a workspace, then work normally:

```bash
# Pull a Box folder locally (FOLDER_ID from Box web UI or `box folders:items 0`)
./scripts/box-init-workspace.sh 123456789 /tmp/box-workspace

# Now just edit files — hooks auto-sync to Box
# When Claude stops responding, the Stop hook prints a sync summary
```

**Explicit mode** — use Box CLI directly with the skill's guidance:

```bash
box search "quarterly report" --json           # Find files
box files:download FILE_ID --destination ./     # Download
box files:upload ./report.md --parent-id 123    # Upload new
box files:versions:upload FILE_ID ./report.md   # Update existing (preserves history)
box files:share FILE_ID --access collaborators  # Share (never defaults to public)
```

## Safety-First Design

Operations are classified by risk level:

- **Read** (always safe) — search, list, download, inspect
- **Create** (verify target) — upload new files, create folders
- **Update** (prefer versions) — modify existing files via version upload
- **Expose** (explicit consent) — sharing links, access level changes
- **Destructive** (explicit request) — delete, bulk reorganize

The skill guides agents toward safe defaults: version uploads over re-uploads, `collaborators` over `open` sharing, manifest-based conflict detection before sync.

## Links

- **Marketplace:** [tonsofskills.com](https://tonsofskills.com)
- **Standalone repo:** [github.com/jeremylongshore/box-cloud-filesystem](https://github.com/jeremylongshore/box-cloud-filesystem)
- **Box CLI:** [github.com/box/boxcli](https://github.com/box/boxcli)
- **Box Developer Docs:** [developer.box.com](https://developer.box.com/)

## License

MIT
