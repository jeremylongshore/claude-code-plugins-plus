---
name: grammarly-cost-tuning
description: |
  Optimize Grammarly costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Grammarly billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "grammarly cost", "grammarly billing",
  "reduce grammarly costs", "grammarly pricing", "grammarly expensive", "grammarly budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Cost Tuning

## Pricing

Grammarly API pricing is enterprise/custom. Contact Grammarly for volume pricing.

## Cost Optimization

### Cache Results

Same text produces same scores — cache aggressively to avoid duplicate API calls.

### Validate Before Calling

```typescript
function shouldScore(text: string): boolean {
  const words = text.split(/\s+/).length;
  if (words < 30) return false; // API will reject
  if (words > 50000) return false; // Too expensive, chunk first
  return true;
}
```

### Sample-Based Scoring

```typescript
// For bulk content, score a sample instead of everything
function selectSample(documents: string[], sampleRate = 0.2): string[] {
  return documents.filter(() => Math.random() < sampleRate);
}
```

### Track Usage

```typescript
let apiCalls = { score: 0, ai: 0, plagiarism: 0 };
// Increment on each call, report daily
```

## Resources

- [Grammarly Enterprise](https://www.grammarly.com/business)

## Next Steps

For architecture, see `grammarly-reference-architecture`.
