---
name: speak-cost-tuning
description: |
  Optimize Speak costs through tier selection, usage monitoring, and efficient lesson design.
  Use when analyzing Speak billing, reducing API costs,
  or implementing usage monitoring and budget alerts for language learning apps.
  Trigger with phrases like "speak cost", "speak billing",
  "reduce speak costs", "speak pricing", "speak expensive", "speak budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Cost Tuning

## Overview
Optimize Speak costs through smart tier selection, efficient lesson design, and usage monitoring.

## Prerequisites
- Access to Speak billing dashboard
- Understanding of current usage patterns
- Database for usage tracking (optional)
- Alerting system configured (optional)

## Instructions
1. **Pricing Model**
2. **Cost Estimation**
3. **Usage Monitoring**
4. **Cost Reduction Strategies**
5. **Budget Alerts Configuration**
6. **Cost Dashboard Query**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Optimized tier selection
- Usage monitoring implemented
- Budget alerts configured
- Cost reduction strategies applied
- Efficient lesson design patterns

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected charges | Untracked usage | Implement monitoring |
| Overage fees | Wrong tier | Upgrade tier |
| Budget exceeded | No alerts | Set up alerts |
| Inefficient audio | No preprocessing | Add client-side optimization |

## Examples
### Quick Cost Check
```typescript
const usage = usageMonitor.getUsageReport();
const estimate = estimateSpeakCost(usage.lessons, usage.audioMinutes, 'personal');

console.log(`Current spend: $${estimate.totalCost.toFixed(2)}`);
console.log(`Base: $${estimate.baseCost} | Overage: $${estimate.overageCost.toFixed(2)}`);

if (estimate.recommendation) {
  console.log(`Recommendation: ${estimate.recommendation}`);
}
```

## Resources
- [Speak Pricing](https://speak.com/pricing)
- [Speak Billing Dashboard](https://developer.speak.com/billing)
- [Usage API](https://developer.speak.com/docs/usage)

## Next Steps
For architecture patterns, see `speak-reference-architecture`.