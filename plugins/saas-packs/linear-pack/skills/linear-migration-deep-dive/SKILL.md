---
name: linear-migration-deep-dive
description: |
  Migrate from Jira, Asana, GitHub Issues, or other tools to Linear.
  Use when planning a migration to Linear, executing data transfer,
  or mapping workflows between tools.
  Trigger with phrases like "migrate to linear", "jira to linear",
  "asana to linear", "import to linear", "linear migration".
allowed-tools: Read, Write, Edit, Bash(node:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive guide for migrating from Jira, Asana, or other issue trackers to Linear, covering assessment, workflow mapping, data export, transformation, batch import, validation, and post-migration reporting.

## Prerequisites
- Admin access to source system (Jira/Asana/GitHub)
- Linear workspace with admin access
- API access to both systems
- Migration timeline and rollback plan

## Instructions

### Step 1: Migration Assessment
Complete the assessment checklist: data volume (issues, projects, users, attachments, custom fields), workflow analysis (statuses, transitions, automations, integrations), user mapping (source to Linear users), and timeline (migration window, parallel run period, cutover date, rollback deadline).

### Step 2: Workflow Mapping
Define status, priority, and issue type mappings for each source system. Jira statuses map to Linear states (e.g., "To Do" -> "Todo", "In Progress" -> "In Progress", "Blocked" -> "In Progress" with label). Jira priorities map to Linear 1-4 scale. Jira issue types become Linear labels. Asana sections map similarly to Linear states.

### Step 3: Export from Source System
Build exporters for each source: `exportJiraProject()` using JQL with pagination (100 per page), fetching summary, description, status, priority, type, assignee, labels, story points, and parent/subtask relations. `exportAsanaProject()` using the Asana SDK to fetch tasks with section names, tags, assignees, and hierarchy. Save exports as timestamped JSON backups.

### Step 4: Transform Data
Create `transformJiraIssue()` that maps each source issue to `LinearIssueInput`: resolve status to stateId, priority to number, assignee email to Linear userId, issue type and labels to labelIds, story points to estimate, and convert Jira markup to Markdown (headers, bold/italic, code blocks, lists, links).

### Step 5: Import to Linear
Build `importToLinear()` that sorts issues by hierarchy (parents first), checks for duplicates, transforms each issue, sets parentId for subtasks, creates via `linearClient.createIssue()`, tracks the sourceId-to-linearId mapping, and respects rate limits (100ms between requests). Track stats: total, created, skipped, errors.

### Step 6: Validation and Post-Migration
Run `validateMigration()` to verify all issues were imported, then sample 50 issues to check title, priority, and state mappings. Generate a migration report with statistics, ID mapping table, and error list. Follow the post-migration checklist: verify critical issues, update integrations, archive source after parallel run, train team.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete Jira/Asana exporters, data transformer with Jira-to-Markdown converter, batch importer with hierarchy sorting, validation script, and migration report generator.

## Output
- Migration assessment checklist
- Workflow mapping tables (status, priority, type)
- Source system exporters (Jira, Asana)
- Data transformer with markup conversion
- Batch importer with hierarchy support
- Validation and migration report

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| User not found | Unmapped user | Add to user mapping |
| Rate limited | Too fast import | Add delays between requests |
| State not found | Unmapped status | Update state mapping |
| Parent not found | Import order wrong | Sort by hierarchy first |

## Examples


**Basic usage**: Apply linear migration deep dive to a standard project setup with default configuration options.

**Advanced scenario**: Customize linear migration deep dive for production environments with multiple constraints and team-specific requirements.

## Resources
- [Linear Import Documentation](https://linear.app/docs/import-issues)
- [Jira API Reference](https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/)
- [Asana API Reference](https://developers.asana.com/reference)

## Next Steps
You have completed the Linear Flagship Skill Pack. You now have comprehensive knowledge of Linear integrations from basic setup through enterprise deployment.