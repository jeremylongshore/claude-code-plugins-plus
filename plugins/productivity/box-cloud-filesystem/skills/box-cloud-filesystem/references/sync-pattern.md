# Workspace Sync Pattern

The agent maintains a local workspace that mirrors a Box folder. Pull before starting, push when done. The manifest makes it safe and repeatable.

## Step 1: Initialize Workspace

```bash
WORKSPACE="/tmp/box-workspace"
BOX_FOLDER_ID="YOUR_FOLDER_ID"  # replace with your actual Box folder ID
mkdir -p "$WORKSPACE"
box folders:download $BOX_FOLDER_ID --destination "$WORKSPACE"
```

Build the manifest — list the folder and capture filename-to-ID mappings:

```bash
box folders:items $BOX_FOLDER_ID --json --fields name,id,content_modified_at > "$WORKSPACE/.box-manifest.json"
```

Or use the init script which does both steps plus configures the hooks:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/box-init-workspace.sh $BOX_FOLDER_ID $WORKSPACE
```

## Step 2: Work Locally

Read, edit, create files inside `$WORKSPACE` using standard file tools. The manifest tracks what came from Box. If hooks are active, edits auto-sync.

## Step 3: Push Changes (Safety Contract)

Before pushing, compare local state against the manifest:

| Local State | Manifest State | Action |
|-------------|---------------|--------|
| File exists, content changed | In manifest | `box files:versions:upload FILE_ID` (version update) |
| New file, not in manifest | Not in manifest | `box files:upload --parent-id FOLDER_ID` (new file) |
| File deleted locally | In manifest | **Do NOT auto-delete from Box** — report to user and ask |
| File renamed locally | In manifest under old name | Treat as new upload + report the rename; do not delete the old one |

**Conflict detection:** before overwriting, check `box files:get FILE_ID --fields content_modified_at`. If the remote file was modified after your download time, warn the user about remote changes before overwriting.

## Step 4: Summarize Before Executing

For non-trivial syncs (more than 5 files), present the plan:

```
Sync plan for Box folder FOLDER_ID:
  UPDATE (version upload): report.md, analysis.py
  NEW (upload): summary.md, charts.png
  SKIP (no changes): data.csv, README.md
  CONFLICT: budget.xlsx (remote modified after download — ask user)
  Proceed? [y/n]
```

## Step 5: Report After Sync

| File | Action | File ID | Status |
|------|--------|---------|--------|
| report.md | version upload | FILE_ID | success |
| summary.md | new upload | FILE_ID | success |
| budget.xlsx | skipped | FILE_ID | conflict — remote newer |

## Examples

### Back up project docs to Box

User says "save my docs folder to Box."

```bash
box users:get --me
box folders:create 0 "my-project-docs" --json
box files:upload docs/README.md --parent-id FOLDER_ID
box files:upload docs/architecture.md --parent-id FOLDER_ID
box files:upload docs/api-spec.md --parent-id FOLDER_ID
box folders:share FOLDER_ID --access collaborators
```

Report: "Uploaded 3 files to Box folder `my-project-docs` (ID: FOLDER_ID). Shared with collaborators."

### Pull dataset, analyze, push results back

```bash
box search "Q1 sales" --type file --json
box files:download FILE_ID --destination /tmp/box-workspace/
# Read CSV locally, generate summary
box files:upload /tmp/box-workspace/q1-sales-summary.md --parent-id PARENT_ID
```

Report: "Downloaded `q1-sales-data.csv` (ID: FILE_ID). Uploaded `q1-sales-summary.md` as new file (ID: NEW_ID) to folder `Q1 Reports` (ID: FOLDER_ID)."

### Workspace sync — edit multiple files

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/box-init-workspace.sh FOLDER_ID /tmp/box-workspace
# Edit files locally — hooks auto-sync each Write/Edit
# For manual sync:
box files:get FILE_ID_1 --fields content_modified_at
box files:versions:upload FILE_ID_1 /tmp/box-workspace/updated-spec.md
box files:versions:upload FILE_ID_2 /tmp/box-workspace/revised-timeline.md
box files:upload /tmp/box-workspace/new-appendix.md --parent-id FOLDER_ID
```

Report:

| File | Action | File ID | Status |
|------|--------|---------|--------|
| updated-spec.md | version upload | FILE_ID | success |
| revised-timeline.md | version upload | FILE_ID | success |
| new-appendix.md | new upload | FILE_ID | success |
