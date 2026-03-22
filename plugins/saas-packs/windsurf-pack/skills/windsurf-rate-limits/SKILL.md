---
name: windsurf-rate-limits
description: |
  Understand and manage Windsurf credit system, usage limits, and model selection.
  Use when running out of credits, optimizing AI usage costs,
  or understanding the credit-per-model pricing structure.
  Trigger with phrases like "windsurf credits", "windsurf rate limit",
  "windsurf usage", "windsurf out of credits", "windsurf model costs".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, credits, pricing, usage]

---
# Windsurf Rate Limits & Credits

## Overview
Windsurf uses a credit-based system for AI features. Each prompt to Cascade consumes credits, with different models costing different amounts. Understanding the credit system prevents mid-session interruptions and optimizes your AI budget.

## Prerequisites
- Windsurf account (Free, Pro, or Teams)
- Access to account dashboard at windsurf.com/account

## Instructions

### Step 1: Understand Credit Allocation by Plan

| Plan | Monthly Credits | Unlimited Features | Price |
|------|----------------|-------------------|-------|
| Free | 25 | Supercomplete (SWE-1 Lite), Tab completions | $0 |
| Pro | 500 | Supercomplete, Tab, Commands, Previews | $15/mo |
| Teams | 500/user | All Pro features + admin controls | $30/user/mo |
| Enterprise | Custom | All features + SSO, RBAC, audit | Custom |

### Step 2: Credit Cost per Model

Different models consume different credit amounts per prompt:

| Model | Credits/Prompt (approx) | Best For |
|-------|------------------------|----------|
| SWE-1 Lite | 0 (unlimited) | Quick questions, simple tasks |
| SWE-1 | 1 | Standard coding tasks |
| SWE-1.5 | 2 | Complex multi-file tasks |
| Claude Sonnet | 2 | Nuanced reasoning, architecture |
| GPT-4o | 2 | General purpose |
| Gemini Pro | 2 | Large context windows |

### Step 3: Monitor Credit Usage

**In-IDE:** Click the Windsurf widget (status bar) > shows remaining credits

**Dashboard:** windsurf.com/account > Usage tab shows:
- Credits consumed today/this month
- Credits remaining
- Per-model breakdown
- Usage trend over time

### Step 4: Credit Conservation Strategies

```markdown
1. Use SWE-1 Lite for simple tasks (free, unlimited):
   - Quick questions about syntax
   - Simple completions
   - Code explanations

2. Use premium models for complex tasks:
   - Multi-file refactoring
   - Architecture decisions
   - Debugging complex issues

3. Write better prompts to reduce back-and-forth:
   - Include file paths, constraints, and expected output
   - Reference files with @ mentions instead of describing them
   - One well-structured prompt > five vague ones

4. Use Workflows for repetitive tasks:
   - Workflows consume credits but eliminate wasted retry prompts
   - A 5-step workflow costs less than 5 separate conversations

5. Leverage free features:
   - Supercomplete (Tab) is unlimited on all plans
   - Command mode (Cmd+I) is unlimited on Pro
   - Only Cascade Write/Chat consumes credits
```

### Step 5: Handle Credit Exhaustion

When credits run out mid-session:

```
1. Switch to SWE-1 Lite (unlimited) for basic tasks
2. Use Supercomplete (Tab) for inline coding -- always free
3. Buy additional credits: windsurf.com/account > Buy Credits
4. Wait for monthly reset (credits renew on billing date)
5. Upgrade plan if consistently running out
```

### Step 6: Team Credit Management (Teams/Enterprise)

```yaml
# Admin Dashboard > Analytics > Credit Usage
team_monitoring:
  total_credits: 5000  # 10 users x 500
  consumed_this_month: 3200
  top_consumers:
    - dev_a: 800 credits (power user)
    - dev_b: 600 credits (heavy Cascade use)
    - dev_c: 50 credits (underutilizing)

  actions:
    - Offer training to dev_c (low usage = not getting value)
    - Review dev_a's usage (is it productive or wasteful?)
    - Consider upgrading if team consistently hits limit
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| "No credits remaining" | Monthly allocation exhausted | Switch to SWE-1 Lite or buy more |
| "Model not available" | Not on required plan tier | Upgrade from Free to Pro |
| Unexpected credit drain | Complex prompts using premium models | Check per-model credit costs |
| Team budget exceeded | No usage monitoring | Enable admin analytics alerts |

## Examples

### Check Credits Quickly
```
Click the Windsurf widget in the bottom-right status bar.
It shows: model name, credits remaining, and authentication status.
```

### Cost-Effective Prompt Strategy
```
Instead of:
1. "What does this function do?" (1 credit)
2. "Can you add error handling?" (1 credit)
3. "Also add tests" (1 credit)
Total: 3 credits

Do this:
1. "Explain this function, add error handling, and write unit tests
   for both success and error paths" (1 credit)
Total: 1 credit
```

## Resources
- [Windsurf Pricing](https://windsurf.com/pricing)
- [Credit Documentation](https://docs.windsurf.com/windsurf/models)

## Next Steps
For security configuration, see `windsurf-security-basics`.
