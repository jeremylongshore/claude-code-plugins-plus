---
name: lindy-performance-tuning
description: |
  Optimize Lindy AI agent execution speed, reliability, and cost efficiency.
  Use when agents are slow, consuming too many credits,
  or producing inconsistent results.
  Trigger with phrases like "lindy performance", "lindy slow",
  "optimize lindy", "lindy latency", "lindy speed".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, performance]

---
# Lindy Performance Tuning

## Overview
Lindy agents execute as multi-step workflows where each step (LLM call, action
execution, API call, condition evaluation) adds latency and credit cost. Optimization
targets: fewer steps, smaller models, faster actions, tighter prompts.

## Prerequisites
- Lindy workspace with active agents
- Access to agent Tasks tab (view step-by-step execution history)
- Understanding of agent workflow structure

## Instructions

### Step 1: Profile Agent Execution
In the Tasks tab, open a completed task and review:
- **Total task duration**: Baseline for improvement
- **Per-step timing**: Identify the slowest steps
- **Credit consumption**: Which steps cost the most
- **Step count**: Total actions executed per task

Common bottlenecks:
| Bottleneck | Symptom | Fix |
|-----------|---------|-----|
| Large model on simple task | High credit cost, slow | Switch to Gemini Flash |
| Too many LLM steps | Long total duration | Consolidate into fewer steps |
| Agent Step with many skills | Unpredictable path | Reduce to 2-4 focused skills |
| Knowledge Base over-querying | Multiple KB searches | Increase Max Results per query |
| Sequential when parallel possible | Unnecessary waiting | Use loop with Max Concurrent > 1 |

### Step 2: Right-Size Model Selection
The single biggest performance lever. Match model to task complexity:

| Task | Recommended Model | Speed | Credits |
|------|-------------------|-------|---------|
| Route email to category | Gemini Flash | Fast | ~1 |
| Extract fields from text | GPT-4o-mini | Fast | ~2 |
| Draft short response | Claude Sonnet | Medium | ~3 |
| Complex multi-step analysis | GPT-4 / Claude Opus | Slow | ~10 |
| Simple phone call | Gemini Flash | Fast | ~20/min |
| Complex phone conversation | Claude Sonnet | Medium | ~20/min |

**Rule of thumb**: Start with the smallest model. Only upgrade if output quality
is insufficient. Most classification and routing tasks work fine with Gemini Flash.

### Step 3: Consolidate LLM Steps
Before (3 LLM calls, ~9 credits):
```
Step 1: Classify email (LLM)
Step 2: Extract key entities (LLM)
Step 3: Generate response (LLM)
```

After (1 LLM call, ~3 credits):
```
Step 1: Classify, extract entities, and generate response (single LLM prompt)
```

Consolidated prompt:
```
Analyze this email and return JSON with:
1. "classification": one of [billing, technical, general]
2. "entities": {customer_name, product, issue_type}
3. "draft_response": professional reply under 150 words

Email: {{email_received.body}}
```

### Step 4: Use Deterministic Actions Where Possible
Replace AI-powered fields with **Set Manually** mode when values are predictable:

| Field | Instead of AI Prompt | Use Set Manually |
|-------|---------------------|------------------|
| Slack channel | "Post to the support channel" | `#support-triage` |
| Email subject | "Create an appropriate subject" | `[Ticket] {{email_received.subject}}` |
| Sheet column | "Determine the right column" | Column A |

Each Set Manually field saves one LLM inference (~1 credit).

### Step 5: Optimize Knowledge Base Queries
- **Max Results**: Set to the minimum needed (default 4, max 10)
- **Search Fuzziness**: Keep at 100 (semantic) unless precision matching needed
- **Query mode**: Use AI Prompt with specific instructions:
  ```
  Search for the customer's specific product issue.
  Focus on: {{extracted_entities.product}} {{extracted_entities.issue_type}}
  ```
  Not: "Search for relevant information" (too vague, wastes results)

### Step 6: Optimize Trigger Filters
Prevent wasted runs with precise trigger filters:
```
Before: Email Received (all emails) → 200 runs/day → 600 credits
After:  Email Received (label: "support" AND NOT from: "noreply@")
        → 30 runs/day → 90 credits (85% savings)
```

### Step 7: Use Agent Steps Judiciously
Agent Steps (autonomous mode) are powerful but expensive — the agent may take
unpredictable paths and use more actions than a deterministic workflow.

**Use Agent Steps when**: Next steps are genuinely uncertain (complex research,
multi-source investigation, adaptive problem-solving)

**Use deterministic actions when**: Steps are predictable (classify -> route -> respond)

**When using Agent Steps**:
- Limit available skills to 2-4
- Set clear, measurable exit conditions
- Include a fallback exit condition to prevent infinite loops
- Monitor credit consumption of first 10 runs to establish baseline

### Step 8: Loop Optimization
For batch processing, configure loops for efficiency:
- **Max Concurrent**: Increase for independent items (parallel execution)
- **Max Cycles**: Always set a cap to prevent runaway processing
- Only pass essential data as loop output (not full context)

## Performance Baseline Reference

| Agent Type | Expected Duration | Expected Credits |
|-----------|------------------|-----------------|
| Simple router (1 LLM + 1 action) | 2-5 seconds | 1-2 |
| Email triage (classify + respond) | 5-15 seconds | 3-5 |
| Research agent (search + analyze) | 15-60 seconds | 5-15 |
| Multi-agent pipeline | 30-120 seconds | 10-30 |
| Phone call | Real-time | ~20/min |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Agent timeout | Too many sequential steps | Consolidate steps, reduce skill count |
| High credit burn | Large model + many steps | Downgrade model, merge LLM calls |
| Inconsistent output | Agent Step choosing different paths | Switch to deterministic workflow |
| KB search slow | Large knowledge base | Reduce fuzziness, increase specificity |
| Loop runs too long | High max cycles, low concurrency | Increase Max Concurrent, lower Max Cycles |

## Resources
- [Lindy Prompt Guide](https://docs.lindy.ai/fundamentals/lindy-101/prompt-guide)
- [Agent Steps](https://docs.lindy.ai/fundamentals/lindy-101/ai-agents)
- [Lindy Documentation](https://docs.lindy.ai)

## Next Steps
Proceed to `lindy-cost-tuning` for budget optimization.
