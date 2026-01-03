# vercel-edge-functions

## Skill Scaffold

```
vercel-edge-functions/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Build and deploy Edge Functions for ultra-low latency API routes running close to users worldwide.
**Workflow:** Secondary workflow after deploy-preview - used when APIs require minimal latency globally.
**Relates to:** Complements vercel-deploy-preview; performance optimizations extend to vercel-performance-tuning

## Summary

This skill enables developers to build and deploy Edge Functions on Vercel's global edge network. Edge Functions run serverless code at locations closest to users, achieving sub-50ms response times. This is ideal for API routes that require minimal latency, such as authentication checks, A/B testing, and personalization logic that must execute before the main application.
