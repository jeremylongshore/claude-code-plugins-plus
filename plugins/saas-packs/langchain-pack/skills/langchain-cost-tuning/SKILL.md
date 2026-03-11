---
name: langchain-cost-tuning
description: |
  Optimize LangChain API costs and token usage.
  Use when reducing LLM API expenses, implementing cost controls,
  or optimizing token consumption in production.
  Trigger with phrases like "langchain cost", "langchain tokens",
  "reduce langchain cost", "langchain billing", "langchain budget".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# LangChain Cost Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Strategies for reducing LLM API costs while maintaining quality in LangChain applications through model tiering, caching, prompt optimization, and budget enforcement.

## Prerequisites
- LangChain application in production
- Access to API usage dashboard
- Understanding of token pricing

## Instructions

### Step 1: Track Token Usage and Costs
Implement a `CostTrackingCallback` that records input/output tokens per request and estimates cost based on model pricing.

### Step 2: Optimize Prompt Length
Use `tiktoken` to count tokens and truncate long prompts. Summarize lengthy context with a dedicated chain when it exceeds the token budget.

### Step 3: Implement Model Tiering
Route simple tasks to cheap models (gpt-4o-mini at $0.15/1M tokens) and complex tasks to powerful models (gpt-4o at $5/1M tokens) using `RunnableBranch`.

### Step 4: Enable Response Caching
Use `RedisSemanticCache` with high similarity threshold (0.95) to avoid duplicate API calls for similar queries.

### Step 5: Set Budget Limits
Implement a `BudgetLimitCallback` that tracks daily spend and raises `RuntimeError` when the budget is exceeded.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete callback code and pricing tables.

## Output
- Token counting and cost tracking
- Prompt optimization utilities
- Model routing for cost efficiency
- Budget enforcement callbacks

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Cost overrun | No budget limits | Enable BudgetLimitCallback |
| Cache misses | Threshold too high | Lower similarity to 0.90 |
| Wrong model selected | Routing logic error | Review task classification |

## Examples
```python
# Cost tracking in 3 lines
tracker = CostTrackingCallback(model="gpt-4o-mini")
llm = ChatOpenAI(model="gpt-4o-mini", callbacks=[tracker])
# After operations:
print(tracker.report())  # {"estimated_cost": "$0.0042", ...}
```

## Resources
- [OpenAI Pricing](https://openai.com/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
- [tiktoken](https://github.com/openai/tiktoken)

## Next Steps
Use `langchain-reference-architecture` for scalable production patterns.
