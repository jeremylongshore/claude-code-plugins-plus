---
name: lindy-core-workflow-b
description: |
  Configure Lindy triggers, scheduling, multi-agent delegation, and automation.
  Use when setting up trigger-based workflows, scheduling agents,
  building multi-agent societies, or configuring agent delegation.
  Trigger with phrases like "lindy automation", "schedule lindy agent",
  "lindy workflow automation", "lindy delegation", "lindy multi-agent".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, workflow]

---
# Lindy Core Workflow B: Triggers & Multi-Agent Automation

## Overview
Configure trigger-based automation, scheduled agents, and multi-agent delegation
("Societies of Lindies"). Covers all trigger types, trigger filters, multiple
triggers per agent, and the Agent Send Message delegation pattern.

## Prerequisites
- Completed `lindy-core-workflow-a` (agent creation)
- Integrations authorized (Gmail, Slack, etc.)
- For delegation: multiple agents created

## Instructions

### Step 1: Configure Trigger Filters
Trigger filters add conditional logic that determines WHICH events wake the agent.
Filters are **not case-sensitive** and support **AND/OR** operators with condition groups.

**Email trigger filter example**:
```
Filter: sender contains "support" AND subject does not contain "auto-reply"
```

**Slack trigger filter example**:
```
Filter: channel equals "#help-desk" AND message contains "urgent"
```

### Step 2: Multiple Triggers (Same Workflow)
One agent can respond to multiple trigger types feeding into the same workflow:
1. Create first trigger (e.g., Webhook Received)
2. Click **"New Trigger"** to add a second (e.g., Email Received)
3. Connect grey arrows from both triggers to the first action step
4. The agent processes both identically

### Step 3: Multiple Workflows (Different Triggers)
A single agent can run entirely different workflows based on trigger type:
- **Trigger A** (Email Received) -> Classify + Draft Reply
- **Trigger B** (Chat Message) -> Search KB + Respond in chat
Each trigger connects to its own action chain.

### Step 4: Schedule-Based Triggers
For recurring automation (daily reports, weekly digests):
1. Add trigger > **Schedule**
2. Configure timing: `Every weekday at 9:00 AM`
3. Options: daily, weekly, monthly, or custom cron
4. The agent runs automatically at the scheduled time

### Step 5: Calendar Event Trigger
For meeting-related automation:
1. Add trigger > **Calendar Event Start**
2. Set **Minutes Offset**:
   - `-30` = trigger 30 minutes BEFORE event
   - `+5` = trigger 5 minutes AFTER event starts
3. Use case: Pre-meeting briefing agent pulls attendee data and sends summary

### Step 6: Multi-Agent Delegation (Societies of Lindies)
Build modular agent systems where specialized agents collaborate:

**Architecture**:
```
[Lead Generator Lindy]
    ↓ Agent Send Message
[Outreach Lindy]
    ↓ Agent Send Message
[Meeting Scheduler Lindy]
```

**Setup**:
1. Give the receiving agent an **Agent Message Received** trigger
2. In the sending agent, add action: **Agent Send Message**
3. Select the target Lindy from the dropdown (shows all agents with Agent triggers)
4. Choose what context to pass — selective context reduces token cost

**Benefits**:
- **Modularity**: Change one agent without affecting others
- **Cost savings**: Send only relevant context, not full history
- **Specialization**: Each agent excels at one task
- **Shared memory**: Societies share memory across tasks

### Step 7: Linked Actions & Channels
**Linked Actions** create downstream execution paths after an action completes:
- Standard linked action: Immediate follow-up (email sent -> log to sheet)
- **Channel**: Listen for future events (email sent -> wait for reply -> process reply)

**Multi-channel example**:
```
Send Email → [Channel: Email Reply Received]
           → [Channel: Slack Message Received]
Each channel maintains its own conversation thread.
```

### Step 8: Looping
For batch processing (e.g., process 50 leads from a spreadsheet):
1. Add a **Loop** step
2. Configure:
   - **Items**: Static list, dynamic data, or AI-generated
   - **Max Cycles**: Limit iterations (prevent runaway)
   - **Max Concurrent**: Parallel execution limit
   - **Output**: Data passed from inside the loop to subsequent steps
3. Only defined loop output is accessible outside the loop

## Trigger Types Quick Reference

| Trigger | Filter Options | Use Case |
|---------|---------------|----------|
| Webhook Received | Headers, body fields | External API integration |
| Email Received | Sender, subject, label | Inbox automation |
| Schedule | Time, recurrence | Recurring reports |
| Chat Message | User, content | Interactive bot |
| Slack Message | Channel, keyword, user | Team automation |
| Agent Message | Sending agent | Multi-agent delegation |
| Calendar Event | Event type, offset | Meeting automation |
| Google Sheets Row | Sheet, column values | Data pipeline |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Trigger fires too often | No filter configured | Add trigger filters with AND/OR conditions |
| Delegation fails | Target agent missing Agent trigger | Add Agent Message Received trigger to target |
| Schedule not firing | Timezone mismatch | Verify timezone in agent settings |
| Loop runs forever | No max cycles set | Always set Max Cycles limit |
| Channel never activates | Reply sent to wrong thread | Verify thread context in channel config |
| Context too large | Passing full history to delegate | Use selective context in Agent Send Message |

## Resources
- [Triggers](https://docs.lindy.ai/fundamentals/lindy-101/triggers)
- [Delegation 101](https://www.lindy.ai/academy-lessons/delegation-101)
- [Action Configuration](https://www.lindy.ai/academy-lessons/action-configuration)

## Next Steps
Proceed to `lindy-common-errors` for troubleshooting.
