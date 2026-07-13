---
name: janitor-fix
description: "Automatically fix skill problems (safe preview first). Also use with --prune to find and remove broken symlinks, empty directories, and orphaned skills. Trigger with '/janitor-fix'."
allowed-tools: Read, Bash(bash:*)
argument-hint: "[--apply] [--prune]"
version: 1.5.1
author: Krzysztof Hendzel <krzysztoff.hendzel@gmail.com>
license: MIT
compatibility: Designed for Claude Code. Requires bash 3.2+ (macOS default works). Modifies only user/project/codex-scope skill files, never plugin content.
tags:
  - skills
  - auto-fix
  - cleanup
  - symlinks
  - maintenance
---

# Auto-Fix

Automatically fix common skill issues. Dry-run by default — shows what would change without modifying files.

## Overview

Repairs frontmatter problems (missing delimiters, empty descriptions, missing version fields) across user, project, and codex-scope skills, and — in `--prune` mode — removes broken symlinks and empty skill directories. Plugin/marketplace skills are never modified (changes would be overwritten on update).

## Prerequisites

- Claude Code with the skills-janitor plugin installed (provides `scripts/fix.sh`)
- bash 3.2+ (the stock macOS bash works; no external dependencies)
- Write access to the user's own skill directories (`~/.claude/skills`, `./.claude/skills`, `~/.agents/skills`)

## Instructions

### Step 1: Preview first (always)

```bash
bash ~/.claude/skills/skills-janitor/scripts/fix.sh            # preview fixes
bash ~/.claude/skills/skills-janitor/scripts/fix.sh --prune    # preview broken/orphaned removals
```

### Step 2: Show the user the preview and confirm

Never jump straight to `--apply`. Present the `[DRY RUN]` lines and ask before writing.

### Step 3: Apply

```bash
bash ~/.claude/skills/skills-janitor/scripts/fix.sh --apply           # apply fixes
bash ~/.claude/skills/skills-janitor/scripts/fix.sh --prune --apply   # remove broken skills
```

What it fixes:

- Adds missing frontmatter delimiters (`---`)
- Fills empty `description` fields with a template
- Adds missing `version` field (defaults to "1.0.0")
- Generates template descriptions using the skill folder name

Prune mode finds and removes:

- **Broken symlinks** — skill folder points to deleted source
- **Empty directories** — skill folder with no SKILL.md
- **Orphaned skills** — user-scope copies of plugin skills

Safety model: dry-run by default (must pass `--apply` to write), skips plugin/marketplace skills, logs ALL changes with timestamps to `data/changelog.log`, always asks for confirmation before removing.

## Output

Per-skill action lines (`[DRY RUN]` / `[FIXED]` / `[PRUNED]` / `[SKIP]`) followed by a summary of fixable issues, skipped items, and prunable entries. In dry-run mode the summary ends with "Run with --apply to make these changes."

## Error Handling

1. **Error**: A fix produced an unexpected result in a SKILL.md
   **Solution**: Every applied change is logged in `data/changelog.log` with a timestamp — show the log entry and restore the affected field manually; template descriptions are meant to be replaced by the author.

2. **Error**: `[SKIP] Plugin/marketplace skill - don't modify`
   **Solution**: Expected behavior, not an error. Plugin content is fixed upstream — suggest the user report the issue to the plugin author instead.

3. **Error**: Prune lists a skill the user wants to keep
   **Solution**: Do not run `--apply`. A "broken symlink" that should be kept means its target moved — recreate the link (`ln -sfn <new-target> <link>`) instead of pruning.

## Examples

### Example 1: Safe fix cycle

**Input**: "Fix my skills."

**Output**: Run the dry-run, present the `[DRY RUN]` list ("3 fixable: 2 missing descriptions, 1 missing version"), ask for confirmation, then run `--apply` and report the `[FIXED]` lines.

### Example 2: Cleanup of broken leftovers

**Input**: "Remove broken skills."

**Output**: Run `--prune` (dry-run), show what would be removed and why (broken symlink targets, empty dirs), confirm, then `--prune --apply` and report the `[PRUNED]` lines.

## Resources

- Fix script (plugin-relative): `{baseDir}/../../scripts/fix.sh`
- Change log of applied fixes: `data/changelog.log` in the plugin directory
- For finding issues: `/janitor-report`
- For usage + token cost: `/janitor-value`
