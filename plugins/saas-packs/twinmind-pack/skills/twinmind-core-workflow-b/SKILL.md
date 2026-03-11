---
name: twinmind-core-workflow-b
description: |
  Execute TwinMind secondary workflow: Action item extraction and follow-up automation.
  Use when automating meeting follow-ups, extracting tasks,
  or integrating with project management tools.
  Trigger with phrases like "twinmind action items",
  "meeting follow-up automation", "extract tasks from meeting".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Core Workflow B: Action Items & Follow-ups

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Secondary workflow for extracting action items with priority/assignee inference, automating follow-up emails, and syncing tasks to project management tools (Asana, Linear, Jira).

## Prerequisites
- Completed `twinmind-core-workflow-a` (transcription)
- Valid transcript or summary available
- Integration tokens for external services (optional)

## Instructions

### Step 1: Extract Action Items
Build `ActionItemExtractor` that calls TwinMind's `/extract/action-items` endpoint with options for context inclusion, speaker-based assignment, and due date inference. Auto-classify priority (high/medium/low) from keywords and categorize items (Review, Development, Communication, Meetings, Documentation).

### Step 2: Automate Follow-up Emails
Create `FollowUpAutomation` with `generateFollowUp()` (AI-generated email with summary + action items), `sendFollowUp()` (immediate send), and `scheduleFollowUp()` (delayed send).

### Step 3: Integrate with Task Management
Implement a `TaskIntegration` interface with `createTask()` and `updateTask()`. Build concrete integrations for Asana (REST API) and Linear (GraphQL) with priority mapping. Use factory pattern via `getTaskIntegration()`.

### Step 4: Orchestrate Complete Follow-up
Wire everything in `runFollowUpWorkflow()`: extract action items, create tasks in external system, then send or schedule follow-up email to attendees.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete ActionItemExtractor, FollowUpAutomation, task integrations, and orchestration code.

## Output
- Extracted action items with assignees and due dates
- Tasks created in project management tool
- Follow-up email sent or scheduled
- Complete audit trail

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| No action items found | Transcript too vague | Verify meeting had clear action items |
| Task creation failed | Invalid project/team ID | Check integration credentials |
| Email send failed | Invalid recipients | Verify email addresses |
| Assignee not found | Name mismatch | Map speakers to user accounts |

## Examples


**Basic usage**: Apply twinmind core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind core workflow b for production environments with multiple constraints and team-specific requirements.

## Supported Integrations

| Service | Tasks | Due Dates | Assignees | Priority |
|---------|-------|-----------|-----------|----------|
| Asana | Yes | Yes | Yes | No |
| Linear | Yes | Yes | Yes | Yes |
| Jira | Yes | Yes | Yes | Yes |
| Notion | Yes | Yes | Yes | No |

## Resources
- [TwinMind Action Items API](https://twinmind.com/docs/action-items)
- [Asana API](https://developers.asana.com)
- [Linear API](https://developers.linear.app)

## Next Steps
For troubleshooting issues, see `twinmind-common-errors`.