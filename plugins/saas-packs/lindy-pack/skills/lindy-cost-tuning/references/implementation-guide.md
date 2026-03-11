# Lindy Cost Tuning - Implementation Guide

# Lindy Cost Tuning

## Overview
Optimize Lindy AI costs by managing active agent count, consolidating automations, and monitoring per-agent execution frequency. Lindy uses per-agent pricing where each active agent incurs a monthly cost regardless of how often it runs. The key cost lever is reducing the number of active agents -- consolidate similar agents, deactivate underused ones, and design multi-purpose agents rather than single-task agents.

## Prerequisites
- Lindy Team or Enterprise workspace
- Admin access to agent management and billing
- Understanding of current agent portfolio

## Instructions

### Step 1: Audit Agent Utilization
```bash
# List all agents with their run counts in the last 30 days
curl "https://api.lindy.ai/v1/agents" \
  -H "Authorization: Bearer $LINDY_API_KEY" | \
  jq '.agents[] | {name: .agent_name, id: .agent_id, status: .status, runs_last_30d: .runs_count_30d, last_run: .last_run_at}' | \
  jq -s 'sort_by(.runs_last_30d)'
# Agents with 0 runs in 30 days are pure cost -- deactivate them
```

### Step 2: Consolidate Similar Agents
```yaml
# Before: 5 separate agents (5x agent cost)
agents_before:
  - "Email classifier - Sales"
  - "Email classifier - Support"
  - "Email classifier - HR"
  - "Email classifier - Marketing"
  - "Email classifier - Legal"

# After: 1 multi-purpose agent (1x agent cost)
agents_after:
  - name: "Universal Email Classifier"
    description: "Routes emails to correct department based on content analysis"
    steps: [classify_content, route_to_department, send_notification]
    # Single agent handles all departments via conditional logic
```

### Step 3: Deactivate Underused Agents
```bash
# Pause agents with <5 runs in the last 30 days
curl -s "https://api.lindy.ai/v1/agents" \
  -H "Authorization: Bearer $LINDY_API_KEY" | \
  jq -r '.agents[] | select(.runs_count_30d < 5 and .status == "active") | .agent_id' | \
  xargs -I{} curl -s -X PATCH "https://api.lindy.ai/v1/agents/{}" \
    -H "Authorization: Bearer $LINDY_API_KEY" \
    -d '{"status": "paused"}'
```

### Step 4: Optimize Agent Step Efficiency
Reduce per-run costs by minimizing the number of tool calls in each agent:
- Combine multiple LLM calls into a single prompt with structured output
- Cache frequently accessed data (e.g., company directory) as agent context
- Use conditional branching to skip unnecessary steps

### Step 5: Monitor Monthly Spend
```bash
# Check current billing and projected costs
curl "https://api.lindy.ai/v1/workspace/billing" \
  -H "Authorization: Bearer $LINDY_API_KEY" | \
  jq '{
    active_agents: .active_agent_count,
    cost_per_agent: .price_per_agent,
    monthly_cost: (.active_agent_count * .price_per_agent),
    runs_this_month: .total_runs_month
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Agent deactivated but still billed | Billing cycle overlap | Check billing date, deactivate before cycle end |
| Consolidated agent too complex | Too many branches | Split into 2-3 focused agents instead of 5+ single-task ones |
| Agent runs increasing cost | Trigger firing too frequently | Adjust trigger schedule or add deduplication |
| Cannot reduce below N agents | Business dependency | Document which agents are critical, optimize the rest |

## Examples
```bash
# Quick ROI check: cost per agent run
curl -s "https://api.lindy.ai/v1/workspace/billing" \
  -H "Authorization: Bearer $LINDY_API_KEY" | \
  jq '{
    monthly_cost: (.active_agent_count * .price_per_agent),
    total_runs: .total_runs_month,
    cost_per_run: ((.active_agent_count * .price_per_agent) / (.total_runs_month + 0.01))
  }'
```
