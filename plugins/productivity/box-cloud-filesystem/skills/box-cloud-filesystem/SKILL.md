---
name: box-cloud-filesystem
description: |
  Cloud filesystem operations via Box CLI. Use when the user mentions
  Box, cloud files, cloud storage, uploading to the cloud, sharing files,
  document management, or syncing project files offsite. Trigger with
  "upload to box", "save to cloud", "pull from box", "search my box files",
  "share this file", "box sync", "cloud backup", or "box filesystem".
allowed-tools: Read, Write, Edit, Bash(box:*), Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
tags: [box, cloud-storage, filesystem, sync, collaboration, document-management]
---

# Box Cloud Filesystem

Two modes, one goal: treat Box like a local filesystem.

**Transparent mode** — initialize a workspace, then every Write or Edit inside it auto-syncs to Box via PostToolUse hooks. No `box` commands needed.

**Explicit mode** — search, download, share, or organize files using Box CLI commands directly. See `references/operations-guide.md` for the full command reference.

## Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Workspace Sync Pattern](#workspace-sync-pattern)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview

Box CLI (`@box/cli`) wraps the full Box API as shell commands. This skill adds three layers:

- **Hooks (transparent sync)** — PostToolUse hooks on Write/Edit auto-upload changed files to Box.
- **Operational judgment** — file identity via numeric IDs, version uploads over duplicates, narrow sharing defaults, manifest-based conflict detection.
- **Sync patterns** — pull/work/push workflow with automatic hook-driven uploads and conflict resolution.

Key principle: **inspect before acting, report after acting.** Folder ID `0` is always root.

## Prerequisites

```bash
npm install --global @box/cli
box login
box users:get --me   # verify auth + enterprise context
```

Auth methods: OAuth (interactive), JWT (automation), CCG (server-to-server), Developer Token (testing, 60 min).

`jq` is required for the hook scripts.

## Instructions

Follow this workflow for every Box operation:

1. **Classify the intent** — discover, read, upload, update, organize, sync, share, or cleanup
2. **Orient** — run `box users:get --me`, identify target folder ID, check the trust zone
3. **Discover** — list or search Box to understand what exists before modifying anything
4. **Execute** — perform the operation (see `references/operations-guide.md` for commands)
5. **Report** — return file IDs, folder IDs, action types, and any conflicts

### Operation Trust Zones

| Zone | Operations | Behavior |
|------|-----------|----------|
| **Read** | search, list, download, metadata | Execute freely |
| **Create** | upload new, create folders | Verify parent folder ID first |
| **Update** | version upload, move, copy | Use file ID, prefer `files:versions:upload` |
| **Expose** | share links, access levels | Default `collaborators`, never `open` unless explicit |
| **Destructive** | delete, bulk reorganize | Only on explicit request; summarize first |

### Safety Rules

1. Inspect folder contents before writing to it.
2. Use file IDs, not filenames, when updating — names are not unique in Box.
3. Prefer `box files:versions:upload FILE_ID` for updates. Avoids 409 conflicts, preserves history.
4. Never delete unless explicitly requested. No "convenience cleanup."
5. Never create `--access open` shared links unless user says "public" or "open."
6. Summarize bulk operations before executing.
7. Report file ID, folder ID, and action type after every write.
8. If unexpected files exist in a folder, stop and ask before modifying.

### Quick Command Reference

```bash
box folders:items FOLDER_ID --json                    # list folder
box search "query" --type file --json                  # search
box files:download FILE_ID --destination ./             # download
box files:upload ./file.txt --parent-id FOLDER_ID       # upload new
box files:versions:upload FILE_ID ./file.txt            # update existing
box files:share FILE_ID --access collaborators          # share (narrow)
box folders:download FOLDER_ID --destination ./         # bulk download
```

Full command reference with examples: `references/operations-guide.md`

## Workspace Sync Pattern

Initialize a workspace, work locally, push changes back. The manifest tracks file IDs.

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/box-init-workspace.sh FOLDER_ID /tmp/box-workspace
```

With hooks active, every Write/Edit auto-syncs. For manual sync, compare local state against the manifest:

- Changed file in manifest → `box files:versions:upload FILE_ID` (version update)
- New file not in manifest → `box files:upload --parent-id FOLDER_ID` (new upload)
- Deleted locally → do NOT auto-delete from Box; ask user
- Conflict detected → warn user before overwriting

Full sync workflow with conflict detection: `references/sync-pattern.md`

## Output

Every write operation returns:

- File/folder ID
- Parent folder ID
- Action type (created / versioned / moved / copied / shared)
- Access level (if sharing)
- Conflicts or skipped items

Read operations return JSON with id, name, size, modified date.

## Error Handling

| Error | Recovery |
|-------|----------|
| `Not Found` (404) | Verify ID with `box search` or re-list parent folder |
| `Conflict` (409) | Use `files:versions:upload` to update, or `--name` for distinct file |
| `Forbidden` (403) | Re-run `box login` or check JWT scopes |
| `Rate Limited` (429) | CLI retries automatically; batch via `--bulk-file-path` |
| `Auth expired` | Run `box login`; use JWT/CCG for production |
| `box: command not found` | `npm install --global @box/cli` |
| Name collision | Use file ID, never filename, to identify targets |
| Local/remote divergence | Re-download, diff, ask user which to keep |

Always report what failed and what succeeded. Never silently skip. Full error table: `references/operations-guide.md`

## Examples

**Back up docs to Box:**
```bash
box folders:create 0 "my-project-docs" --json
box files:upload docs/README.md --parent-id FOLDER_ID
box folders:share FOLDER_ID --access collaborators
```

**Pull, analyze, push back:**
```bash
box search "Q1 sales" --type file --json
box files:download FILE_ID --destination /tmp/box-workspace/
# analyze locally, then push result
box files:upload /tmp/box-workspace/summary.md --parent-id PARENT_ID
```

**Workspace sync (with hooks):**
```bash
${CLAUDE_PLUGIN_ROOT}/scripts/box-init-workspace.sh FOLDER_ID /tmp/box-workspace
# edit files normally — hooks auto-sync to Box
```

More detailed examples: `references/sync-pattern.md`

## Resources

- Box CLI: https://github.com/box/boxcli
- Box Developer Docs: https://developer.box.com/
- Box API Reference: https://developer.box.com/reference/
- Box pricing: https://www.box.com/ (free tier available for individual users)
