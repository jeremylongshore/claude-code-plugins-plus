---
name: lindy-cost-tuning
description: |
  Optimize Lindy AI costs through credit management, model selection,
  and agent consolidation.
  Use when reducing spend, analyzing credit usage patterns,
  or optimizing budget allocation across agents.
  Trigger with phrases like "lindy cost", "lindy billing",
  "reduce lindy spend", "lindy budget", "lindy credits".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, cost-optimization]

---
# Lindy Cost Tuning

## Overview
Lindy uses a credit-based pricing model. Every task costs credits based on model
size, step count, premium actions, and duration. Cost tuning targets: model
right-sizing, agent consolidation, trigger optimization, and credit monitoring.

## Prerequisites
- Lindy workspace with billing access
- Multiple active agents to evaluate
- Dashboard access to review per-agent task history

## Credit Cost Reference

| Factor | Credits |
|--------|---------|
| Basic model task (Gemini Flash) | 1-2 |
| Mid-tier model (GPT-4o-mini, Claude Haiku) | 2-5 |
| Large model task (GPT-4, Claude Sonnet) | 5-10 |
| Premium model (Claude Opus) | ~10+ |
| Phone call (US/Canada) | ~20/minute |
| Phone call (international) | 21-53/minute |
| Premium actions (webhooks) | Additional per action |
| Minimum per task | 1 credit |

## Plan Costs

| Plan | Monthly | Credits | Per Extra Seat |
|------|---------|---------|----------------|
| Free | $0 | 400 | N/A |
| Pro | $49.99 | 5,000 | $19.99 |
| Business | $299.99 | 30,000 | Included |
| Enterprise | Custom | Custom | Custom |

## Instructions

### Step 1: Audit Agent Credit Consumption
For each active agent, collect:
1. **Task count** (last 30 days) — from Tasks tab
2. **Average credits per task** — total credits / task count
3. **Model used** — from agent settings
4. **Trigger frequency** — how often the agent fires

Create a cost audit table:
| Agent | Tasks/Month | Credits/Task | Model | Monthly Credits | % of Total |
|-------|------------|-------------|-------|----------------|-----------|
| Support Bot | 500 | 5 | Claude Sonnet | 2,500 | 50% |
| Lead Router | 200 | 2 | GPT-4o-mini | 400 | 8% |
| Report Gen | 30 | 10 | GPT-4 | 300 | 6% |

### Step 2: Right-Size Models
The highest-impact optimization. For each agent, ask:
> "Does this task actually need GPT-4/Claude, or would Gemini Flash work?"

| Current Setup | Optimized | Savings |
|--------------|-----------|---------|
| Email classify with Claude Sonnet (5 cr) | Gemini Flash (1 cr) | 80% |
| Data extract with GPT-4 (10 cr) | GPT-4o-mini (3 cr) | 70% |
| Simple routing with Claude Opus (10 cr) | Gemini Flash (1 cr) | 90% |

**Test the downgrade**: Run 10 tasks with the smaller model. Compare output quality.
Most classification, routing, and extraction tasks work identically on smaller models.

### Step 3: Consolidate Redundant Agents
Multiple single-purpose agents cost more than one multi-purpose agent:

Before (5 agents, 5 minimum credits per run):
```
Agent 1: Classify billing emails
Agent 2: Classify technical emails
Agent 3: Classify general emails
Agent 4: Draft billing responses
Agent 5: Draft technical responses
```

After (1 agent, 1 minimum credit per run):
```
Support Agent: Classify email → Condition (billing/technical/general)
  → Draft appropriate response → Send
```

**Cost impact**: Reducing from 5 agents to 1 saves minimum-credit overhead and
simplifies management.

### Step 4: Optimize Trigger Frequency
Credits are consumed every time a trigger fires. Reduce unnecessary triggers:

**Email Received**:
```
Before: Trigger on ALL emails (300/day) = 300 tasks
After:  Filter: label "support" AND NOT from "noreply@" (40/day) = 40 tasks
Savings: 87% fewer tasks
```

**Schedule trigger**:
```
Before: Every 15 minutes (96/day)
After:  Every 2 hours (12/day)
Question: Does this agent really need to run every 15 minutes?
```

**Slack trigger**:
```
Before: Any message in #general (200/day)
After:  Messages containing "@support-bot" (10/day)
Savings: 95% fewer tasks
```

### Step 5: Reduce Steps Per Task
Each action in a workflow costs credits. Eliminate unnecessary steps:
- Combine multiple LLM calls into one (see `lindy-performance-tuning`)
- Use Set Manually instead of AI Prompt for known values
- Remove debug/logging steps in production
- Simplify condition branches

### Step 6: Optimize Knowledge Base Usage
KB search costs credits per query. Optimize:
- Reduce Max Results from 10 to 4 (sufficient for most queries)
- Use specific query instructions to get relevant results in one search
- For small datasets (<100 entries), consider putting data directly in the prompt

### Step 7: Budget Monitoring Setup
1. Check credit usage weekly in **Settings > Billing**
2. Set internal alerts for high-consumption agents:
   - 50% of budget: Warning — review usage
   - 80% of budget: Alert — optimize or upgrade
   - 95% of budget: Critical — pause non-essential agents

### Step 8: Deactivate Idle Agents
Review agents monthly:
- No tasks in 30 days → Pause the agent
- No tasks in 90 days → Delete or archive
- Lindy only charges for active agent execution, not idle agents

## Monthly Cost Optimization Checklist
- [ ] Review per-agent credit consumption
- [ ] Identify agents using large models for simple tasks
- [ ] Check for redundant agents that could be consolidated
- [ ] Review trigger filter effectiveness
- [ ] Remove unused integrations from agents
- [ ] Verify no loops or runaway agent steps
- [ ] Compare actual spend to budget

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected credit spike | Trigger filter removed or loosened | Review and restore trigger filters |
| Agent consuming 10x normal | Looping agent step | Add exit conditions, check task history |
| Credits exhausted mid-month | Under-budgeted or spike | Upgrade plan or pause non-critical agents |
| Model downgrade hurts quality | Task needs larger model | Selectively upgrade only that step |

## Resources
- [Lindy Pricing](https://www.lindy.ai/pricing)
- [Lindy Documentation](https://docs.lindy.ai)

## Next Steps
Proceed to `lindy-reference-architecture` for production architecture patterns.
