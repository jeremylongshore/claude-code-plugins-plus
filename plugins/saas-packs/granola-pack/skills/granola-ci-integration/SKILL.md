---
name: granola-ci-integration
description: |
  Configure Granola CI/CD integration with automated workflows.
  Use when setting up automated meeting note processing,
  integrating with development pipelines, or building Zapier automations.
  Trigger with phrases like "granola CI", "granola automation pipeline",
  "granola workflow", "automated granola", "granola DevOps".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Granola CI Integration

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Build automated workflows that process Granola meeting notes into GitHub issues, Linear tasks, Slack notifications, and documentation updates.

## Prerequisites
- Granola Pro or Business plan
- Zapier account
- GitHub repository (for Actions)
- Development workflow understanding

## Instructions

### Step 1: Set Up Zapier Trigger
Create Zap with Granola "New Note Created" trigger. Add filter for meeting type (sprint, planning, etc.).

### Step 2: Parse Action Items
Use Zapier Code step to extract action items with assignees from note content using regex patterns.

### Step 3: Create GitHub Issues
Route parsed action items to GitHub as labeled issues with meeting context.

### Step 4: Configure GitHub Actions Workflow
Create `repository_dispatch` workflow triggered by Zapier to update meeting logs and create issues programmatically.

### Step 5: Add Linear Integration
Auto-create Linear tasks from action items with team assignment and meeting context.

### Step 6: Set Up Slack Notifications
Post meeting summaries with action items and "View Full Notes" button to team channels.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for Zapier code steps, GitHub Actions workflow YAML, Linear pipeline config, and Slack bot message format.

## Output
- Zapier pipeline processing meeting notes automatically
- GitHub issues created from action items
- Meeting log updated in repository
- Slack notifications sent to team channels

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Webhook timeout | Large payload | Add processing delay step |
| Auth expired | Token invalid | Refresh OAuth tokens in Zapier |
| Rate limited | Too many requests | Add delays between actions |
| Parse failed | Note format changed | Update parsing regex logic |

## Examples

### Integration Test Checklist
- [ ] Schedule test meeting with sample action items
- [ ] Verify Zapier trigger fires
- [ ] Check GitHub issues created with correct labels
- [ ] Confirm Slack notification sent to channel
- [ ] Validate Linear tasks appear in correct team

## Resources
- [Zapier Webhooks](https://zapier.com/help/create/code-webhooks)
- [GitHub Actions Events](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows)

## Next Steps
Proceed to `granola-deploy-integration` for native app integrations.
