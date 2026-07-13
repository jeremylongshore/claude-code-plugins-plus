# Step 3: Hybrid Architecture

Deep-dive reference for the `figma-architecture-variants` skill — extracted from the 'Step 3: Hybrid Architecture' step of the workflow.

Many production systems combine variants:

```
CLI (CI) ← Scheduled token sync (daily at 9 AM)
     +
Webhook Service ← Real-time notifications (Slack, rebuild triggers)
     +
Figma Plugin ← In-editor design linting and data population
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
