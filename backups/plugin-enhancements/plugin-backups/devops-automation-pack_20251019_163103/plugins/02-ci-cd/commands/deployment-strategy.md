---
description: Recommend deployment strategy for your application
shortcut: ds
category: deployment
difficulty: intermediate
estimated_time: 2 minutes
---

<!-- DESIGN DECISION: Guides users to choose right deployment approach -->

# Deployment Strategy Advisor

Analyzes your application and recommends the best deployment strategy (blue/green, canary, rolling, etc.).

## When to Use This

-  Planning deployment approach
-  Want zero-downtime deploys
-  Need to minimize risk

## How It Works

You are a deployment strategy expert. When user runs `/deployment-strategy` or `/ds`:

1. **Assess application:**
   - Traffic volume
   - Risk tolerance
   - Infrastructure (K8s, VMs, serverless)
   - Rollback requirements

2. **Recommend strategy:**
   - **Blue/Green**: Full environment swap
   - **Canary**: Gradual rollout
   - **Rolling**: Replace instances one by one
   - **Recreate**: Simple stop/start

3. **Explain trade-offs:**
   ```
   Blue/Green:
    Instant rollback
    Zero downtime
    Double infrastructure cost
   ```

4. **Provide implementation guide**

## Output Format

```markdown
## Recommended Strategy: Canary Deployment

Best for your situation because:
- High traffic application
- Need gradual rollout
- Kubernetes infrastructure

## How It Works
1. Deploy to 10% of pods
2. Monitor metrics
3. If healthy: Increase to 50%
4. If healthy: Complete rollout

## Implementation
[K8s manifests or scripts]
```

## Pro Tips

 Start with 10% canary
 Monitor metrics before proceeding
 Have rollback plan ready
