# Step 4: Cost-Saving Architecture

Deep-dive reference for the `figma-cost-tuning` skill — extracted from the 'Step 4: Cost-Saving Architecture' step of the workflow.

```
Polling Architecture (expensive):
  App → GET /v1/files/:key every 30s → 2,880 calls/day/file

Webhook Architecture (efficient):
  Figma → POST /webhooks/figma (only when file changes)
  App → GET /v1/files/:key (only after webhook) → ~10-50 calls/day/file

Savings: 95%+ fewer API calls
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
