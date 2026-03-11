---
name: klingai-cost-controls
description: |
  Implement cost controls and budget management for Kling AI. Use when managing spending limits,
  tracking costs, or preventing budget overruns. Trigger with phrases like 'klingai cost',
  'kling ai budget', 'klingai spending', 'video generation costs'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Klingai Cost Controls

## Overview

This skill teaches how to implement cost controls, budget tracking, usage alerts, and spending limits for Kling AI video generation to prevent unexpected charges.

## Prerequisites

- Kling AI API key configured
- Understanding of Kling AI pricing model
- Python 3.8+

## Instructions

Follow these steps for cost management:

1. **Understand Pricing**: Learn cost structure
2. **Set Budgets**: Define spending limits
3. **Track Usage**: Monitor consumption
4. **Create Alerts**: Set up notifications
5. **Enforce Limits**: Implement hard stops

## Output

Successful execution produces:
- Cost tracking records
- Budget limit enforcement
- Usage alerts at thresholds
- Prevented budget overruns

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Pricing](https://klingai.com/pricing)
- [Usage Dashboard](https://console.klingai.com/usage)
- [Billing Documentation](https://docs.klingai.com/billing)
