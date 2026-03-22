---
name: fathom-cost-tuning
description: |
  Optimize Fathom API usage and plan selection.
  Trigger with phrases like "fathom cost", "fathom pricing", "fathom plan".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Cost Tuning

## Plan Comparison

| Feature | Free | Team |
|---------|------|------|
| AI summaries | Unlimited | Unlimited |
| API access | Yes | Yes |
| Team sharing | No | Yes |
| CRM integration | No | Yes |
| Webhooks | Yes | Yes |

## API Optimization

- Use webhooks to receive data push (no polling cost)
- Cache transcripts locally (they do not change)
- Use `include_summary=true` in list requests to avoid extra calls
- Batch processing within 60 req/min limit

## Resources

- [Fathom Pricing](https://fathom.video/pricing)

## Next Steps

For architecture, see `fathom-reference-architecture`.
