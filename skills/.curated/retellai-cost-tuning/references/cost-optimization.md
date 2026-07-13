# Cost Optimization Examples

## Analyze Call Duration Distribution

```bash
set -euo pipefail
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

## Set Maximum Call Duration

```bash
set -euo pipefail
# Prevent runaway costs from calls that loop or get stuck
curl -X PATCH "https://api.retellai.com/v1/agents/agt_abc123" \
  -H "Authorization: Bearer $RETELL_API_KEY" \
  -d '{
    "max_call_duration_seconds": 300,
    "end_call_after_silence_seconds": 15
  }'
# 5-minute cap prevents a single call from costing more than ~$0.50
```

## Conversation Design Patterns for Brevity

```yaml
# Conversation design patterns that reduce call duration
fast_resolution_patterns:
  greeting:
    bad: "Hello! Welcome to Company. How are you doing today? I hope you're having a great day."  # 8 seconds
    good: "Hi, this is Company. What can we do for you?"  # 3 seconds
    savings: "5 seconds per call * 1000 calls/month = 83 minutes saved"

  confirmation:
    bad: "Let me repeat that back to you to make sure I have it right..."  # Long
    good: "Got it. Anything else?"  # Short
    savings: "10 seconds per interaction"

  closing:
    bad: "Thank you so much for calling. Is there anything else I can assist with today?"
    good: "All set. Goodbye!"
    savings: "5 seconds per call"
```

## LLM Backend Selection

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

# Do not use expensive models for simple routing tasks
```

## Daily Cost Monitoring

```bash
set -euo pipefail
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
