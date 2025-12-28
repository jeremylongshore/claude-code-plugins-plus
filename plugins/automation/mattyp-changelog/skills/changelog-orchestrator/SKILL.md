---
name: changelog-orchestrator
description: Draft changelog PRs by collecting GitHub/Slack/Git changes, formatting with templates, running quality gates, and preparing a branch/PR. Use when generating weekly/monthly release notes or when the user asks to create a changelog from recent merges. Trigger with "changelog weekly", "generate release notes", "draft changelog", "create changelog PR".
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(git:*), Bash(gh:*), Bash(python:*), Bash(date:*)"
version: "0.1.0"
author: "Mattyp <mattyp@claudecodeplugins.io>"
license: "MIT"
---

# Changelog Orchestrator

Automate changelog generation with a predictable 6‑phase workflow: fetch → synthesize → format → quality gate → PR → handoff.

## Overview

This skill turns raw repo activity (merged PRs, issues, commits, optional Slack updates) into a publishable changelog draft and prepares a branch/PR for review.

## Prerequisites

- A project config file at `.changelog-config.json` in the target repo.
- Required environment variables set (at minimum `GITHUB_TOKEN` for GitHub source).
- Git available in PATH; `gh` optional (used for PR creation if configured).

## Instructions

### Phase 1: Initialize & Load Config

1. Read `.changelog-config.json` from the repo root.
2. Validate it with `{baseDir}/scripts/validate_config.py`.
3. Decide date range:
   - Weekly mode: today minus 7 days → today
   - Custom mode: use provided `start_date`/`end_date`

### Phase 2: Fetch Changelog Inputs

Collect items from configured sources:
- GitHub: merged PRs + closed issues in date range (labels filtering if configured)
- Slack (optional): messages from configured channels
- Git: commit log summary (conventional commits if enabled)

If a live API isn’t available, still proceed with Git-only changes and record gaps in the final draft.

### Phase 3: AI Synthesis (Narrative Draft)

Create a first draft that:
- Groups changes into **Highlights**, **Features**, **Fixes**, **Breaking Changes**, **Internal/Infra**
- Uses a user-facing tone (clear outcomes, minimal jargon)
- Links back to PRs/issues when URLs are present

### Phase 4: Template Formatting + Frontmatter

1. Load the configured markdown template (or fall back to `{baseDir}/assets/weekly-template.md`).
2. Render the final markdown using `{baseDir}/scripts/render_template.py`.
3. Ensure frontmatter contains at least `date` (ISO) and `version` (SemVer if known; otherwise `0.0.0`).

### Phase 5: Quality Gate (Deterministic + Editorial)

1. Run deterministic checks using `{baseDir}/scripts/quality_score.py`.
2. If score is below threshold:
   - Fix structural issues first (missing sections, broken links, invalid frontmatter)
   - Rewrite only the weakest sections (max 2 iterations)

### Phase 6: PR Creation + User Handoff

1. Write the changelog file to the configured `output_path`.
2. Create a branch `changelog-YYYY-MM-DD`, commit with `docs: add changelog for YYYY-MM-DD`.
3. If `gh` is configured, open a PR; otherwise, print the exact commands the user should run.

## Output

- A markdown changelog draft (usually `CHANGELOG.md`), plus an optional PR URL.
- A quality report (score + findings) from `{baseDir}/scripts/quality_score.py`.

## Error Handling

- Missing config: instruct the user to copy `${CLAUDE_PLUGIN_ROOT}/config/changelog-config.example.json` to `.changelog-config.json`.
- Missing token env var: show which `token_env` is required and how to export it.
- Missing template: fall back to `{baseDir}/assets/default-changelog.md` and note it in output.
- No changes found: produce an empty changelog with a short “No user-visible changes” note.

## Examples

### Weekly changelog

User: “Generate the weekly changelog and open a PR”

Expected behavior: compute last 7 days, draft changelog, pass quality gate, create branch and PR.

### Custom range changelog

User: “Generate changelog from 2025-12-01 to 2025-12-15”

Expected behavior: use that range, draft changelog, and prepare PR.

## Resources

- Validate config: `{baseDir}/scripts/validate_config.py`
- Render template: `{baseDir}/scripts/render_template.py`
- Quality scoring: `{baseDir}/scripts/quality_score.py`
- Default templates:
  - `{baseDir}/assets/default-changelog.md`
  - `{baseDir}/assets/weekly-template.md`
  - `{baseDir}/assets/release-template.md`

