---
name: lindy-core-workflow-b
description: |
  Core Lindy workflow for automating tasks and scheduling agents.
  Use when setting up automated workflows, scheduling agent runs,
  or creating trigger-based automations.
  Trigger with phrases like "lindy automation", "schedule lindy agent",
  "lindy workflow automation", "automate with lindy".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lindy Core Workflow B: Task Automation

## Overview
Complete workflow for automating tasks and scheduling Lindy AI agents.

## Prerequisites
- Completed `lindy-core-workflow-a` (agent creation)
- Agent ID ready for automation
- Clear automation requirements defined

## Instructions

### Step 1: Define Automation Spec
### Step 2: Create Scheduled Automation
### Step 3: Create Webhook Trigger
### Step 4: Create Email Trigger

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Configured automation triggers
- Scheduled or event-based agent runs
- Webhook endpoints for external triggers
- Email triggers for inbox automation

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid cron | Bad schedule format | Use standard cron syntax |
| Webhook conflict | Path already used | Choose unique webhook path |
| Agent not found | Invalid agent ID | Verify agent exists |

## Examples

### Multi-Trigger Setup
## Resources
- [Lindy Automations](https://docs.lindy.ai/automations)
- [Cron Syntax](https://docs.lindy.ai/automations/cron)
- [Webhook Guide](https://docs.lindy.ai/automations/webhooks)

## Next Steps
Proceed to `lindy-common-errors` for troubleshooting guidance.
