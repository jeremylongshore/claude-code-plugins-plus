---
name: clerk-performance-tuning
description: |
  Optimize Clerk authentication performance.
  Use when improving auth response times, reducing latency,
  or optimizing Clerk SDK usage.
  Trigger with phrases like "clerk performance", "clerk optimization",
  "clerk slow", "clerk latency", "optimize clerk".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk Performance Tuning

## Overview
Optimize Clerk authentication for best performance and user experience.

## Prerequisites
- Clerk integration working
- Performance monitoring in place
- Understanding of application architecture

## Instructions
- Step 1: Optimize Middleware
- Step 2: Implement User Data Caching
- Step 3: Optimize Token Handling
- Step 4: Lazy Load Auth Components
- Step 5: Optimize Server Components
- Step 6: Edge Runtime Optimization

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Optimized middleware configuration
- Multi-level caching strategy
- Token management optimization
- Lazy loading for auth components

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow page loads | Blocking auth calls | Use Suspense boundaries |
| High latency | No caching | Implement token/user cache |
| Bundle size | All components loaded | Lazy load auth components |
| Cold starts | Node runtime | Use Edge runtime |

## Resources
- [Next.js Performance](https://nextjs.org/docs/app/building-your-application/optimizing)
- [Clerk Performance Tips](https://clerk.com/docs/quickstarts/nextjs)
- [Edge Runtime](https://nextjs.org/docs/app/api-reference/edge)

## Next Steps
Proceed to `clerk-cost-tuning` for cost optimization strategies.
