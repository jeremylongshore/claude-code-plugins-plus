# Lindy Performance Tuning - Implementation Guide

# Lindy AI Performance Tuning

## Overview
Optimize Lindy AI agent execution speed and reliability. Lindy agents run as multi-step automations where each step (LLM call, tool execution, API call) adds latency. A typical 5-step agent takes 10-30 seconds total. The biggest performance levers are: reducing step count (combine LLM calls), using faster tool configurations, implementing parallel step execution where possible, and caching frequently-accessed data in agent memory.

## Prerequisites
- Lindy workspace with active agents
- Access to agent configuration and run history
- Understanding of agent step execution flow

## Instructions

### Step 1: Identify Slow Steps
```bash
# Analyze step-level timing for recent agent runs
curl "https://api.lindy.ai/v1/runs?limit=20&expand=steps" \
  -H "Authorization: Bearer $LINDY_API_KEY" | \
  jq '.runs[] | {agent: .agent_name, total_ms: .duration_ms, steps: [.steps[] | {name: .step_name, duration_ms: .duration_ms, status}]} | {agent, total_ms, slowest_step: (.steps | max_by(.duration_ms))}'
```

### Step 2: Consolidate LLM Steps
```yaml
# Before: 3 separate LLM calls (3 * 2-5s = 6-15s total)
steps_before:
  - name: "Classify email"
    type: llm_call
    prompt: "Classify this email as sales/support/spam"
  - name: "Extract entities"
    type: llm_call
    prompt: "Extract company name and person from email"
  - name: "Draft response"
    type: llm_call
    prompt: "Draft a response to this email"

# After: 1 LLM call with structured output (2-5s total)
steps_after:
  - name: "Process email"
    type: llm_call
    prompt: |
      Analyze this email and return JSON:
      {"classification": "sales|support|spam", "company": "", "person": "", "draft_response": ""}
# Saves: 4-10 seconds per run
```

### Step 3: Cache Agent Context Data
```yaml
# Instead of fetching reference data every run:
# Store frequently-accessed data as agent memory
agent_memory:
  team_directory:
    refresh: daily
    data: "List of team members, roles, and email addresses"
  product_catalog:
    refresh: weekly
    data: "Current product names, prices, and descriptions"
  faq_responses:
    refresh: weekly
    data: "Common customer questions and approved responses"
# Eliminates 1-3 API calls per run
```

### Step 4: Parallelize Independent Steps
```yaml
# Steps that don't depend on each other should run in parallel
parallel_execution:
  step_group_1:
    parallel: true
    steps:
      - "Fetch CRM data"       # API call: 500ms
      - "Fetch calendar data"   # API call: 300ms
      - "Fetch email thread"    # API call: 400ms
    # Parallel: 500ms total (max of 3)
    # Sequential: 1200ms total (sum of 3)

  step_group_2:
    depends_on: step_group_1
    steps:
      - "Analyze combined data"  # LLM call: 2-5s
```

### Step 5: Optimize Trigger Configuration
```yaml
# Reduce unnecessary agent invocations
trigger_optimization:
  email_trigger:
    bad: "Trigger on every email received"
    good: "Trigger only on emails from known contacts, skip newsletters"
    filter: "from != *@newsletter.* AND from != *@noreply.*"

  schedule_trigger:
    bad: "Run every 5 minutes"
    good: "Run every 30 minutes (batch process)"
    impact: "6x fewer runs, same total throughput"
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Agent timeout (>60s) | Too many sequential steps | Consolidate steps, add parallel execution |
| Step retry loop | Transient API failure | Set max retries to 2, add fallback step |
| Slow LLM step | Prompt too long or complex | Shorten prompt, use focused instructions |
| High run frequency | Trigger firing too often | Add filters to trigger configuration |

## Examples
```bash
# Benchmark: average agent run time over last 50 runs
curl -s "https://api.lindy.ai/v1/runs?limit=50" \
  -H "Authorization: Bearer $LINDY_API_KEY" | \
  jq '{
    avg_duration_ms: ([.runs[].duration_ms] | add / length),
    p95_duration_ms: ([.runs[].duration_ms] | sort | .[47]),
    slowest_agent: (.runs | max_by(.duration_ms) | {agent: .agent_name, ms: .duration_ms})
  }'
```
