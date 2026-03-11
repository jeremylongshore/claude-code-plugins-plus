---
name: retellai-cost-tuning
description: |
  Optimize Retell AI costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Retell AI billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "retellai cost", "retellai billing",
  "reduce retellai costs", "retellai pricing", "retellai expensive", "retellai budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Retell AI Cost Tuning

## Overview
Reduce Retell AI voice agent costs by optimizing call duration, choosing the right voice model, and implementing conversation design patterns that resolve calls faster. Retell charges per minute of voice call with rates varying by model and voice quality. The biggest cost levers are: reducing average call duration through better conversation design (a 2-minute call costs half of a 4-minute call), using faster/cheaper LLM backends for simple tasks, and setting maximum call duration limits to prevent runaway costs.

## Prerequisites
- Retell AI dashboard access with billing visibility
- Understanding of agent call patterns and average durations
- Ability to modify agent prompts and configurations

## Instructions

### Step 1: Analyze Call Duration Distribution
```bash
# Find agents with longest average call durations (highest cost)
curl "https://api.retellai.com/v1/calls?limit=200&sort=-created_at" \
  -H "Authorization: Bearer $RETELL_API_KEY" | \
  jq 'group_by(.agent_id) | map({
    agent: .[0].agent_name,
    calls: length,
    avg_duration_sec: ([.[].duration] | add / length),
    total_minutes: ([.[].duration] | add / 60),
    estimated_cost: ([.[].cost] | add)
  }) | sort_by(-.estimated_cost)'
```

### Step 2: Set Maximum Call Duration
```bash
# Prevent runaway costs from calls that loop or get stuck
curl -X PATCH "https://api.retellai.com/v1/agents/agt_abc123" \
  -H "Authorization: Bearer $RETELL_API_KEY" \
  -d '{
    "max_call_duration_seconds": 300,
    "end_call_after_silence_seconds": 15
  }'
# 5-minute cap prevents a single call from costing more than ~$0.50
```

### Step 3: Optimize Conversation Design for Brevity
```yaml
# Conversation design patterns that reduce call duration
fast_resolution_patterns:
  greeting:
    bad: "Hello! Welcome to Company. How are you doing today? I hope you're having a great day."  # 8 seconds
    good: "Hi, this is Company. How can I help?"  # 3 seconds
    savings: "5 seconds per call * 1000 calls/month = 83 minutes saved"

  confirmation:
    bad: "Let me repeat that back to you to make sure I have it right..."  # Long
    good: "Got it. Anything else?"  # Short
    savings: "10 seconds per interaction"

  closing:
    bad: "Thank you so much for calling. Is there anything else I can help you with today?"
    good: "All set. Goodbye!"
    savings: "5 seconds per call"
```

### Step 4: Use Cheaper LLM Backends for Simple Tasks
```yaml
# Agent configuration: match LLM cost to task complexity
simple_agents:  # FAQ, routing, appointment scheduling
  llm: "fast/cheap model"
  expected_duration: "30-90 seconds"
  cost_per_call: "~$0.05-0.10"

complex_agents:  # Sales qualification, technical support
  llm: "smart/capable model"
  expected_duration: "2-5 minutes"
  cost_per_call: "~$0.20-0.50"

# Don't use expensive models for "press 1 for sales" routing
```

### Step 5: Monitor Daily Costs
```bash
# Daily cost tracking with anomaly detection
curl -s "https://api.retellai.com/v1/calls?created_after=$(date -I)" \
  -H "Authorization: Bearer $RETELL_API_KEY" | \
  jq '{
    calls_today: length,
    total_minutes: ([.[].duration] | add / 60),
    total_cost: ([.[].cost] | add),
    avg_cost_per_call: (([.[].cost] | add) / length),
    projected_monthly: (([.[].cost] | add) * 30)
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High per-call cost | Agent prompts too verbose | Shorten greetings, confirmations, closings |
| Stuck calls burning minutes | Agent in conversation loop | Set `max_call_duration_seconds` |
| Cost spike from one agent | Agent handling unexpected topic | Add fallback to transfer to human |
| Budget exceeded | No daily spending cap | Implement daily cost monitoring with alerts |

## Examples
```bash
# ROI calculator: cost per successful outcome
TOTAL_COST=$(curl -s "https://api.retellai.com/v1/calls?created_after=$(date -d '30 days ago' -I)" \
  -H "Authorization: Bearer $RETELL_API_KEY" | jq '[.[].cost] | add')
SUCCESSFUL=$(curl -s "https://api.retellai.com/v1/calls?created_after=$(date -d '30 days ago' -I)&status=completed" \
  -H "Authorization: Bearer $RETELL_API_KEY" | jq 'length')
echo "Cost per successful call: \$$(echo "$TOTAL_COST / $SUCCESSFUL" | bc -l | head -c 5)"
```
