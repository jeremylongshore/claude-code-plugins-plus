# Pitfall 8: Polling Instead of Webhooks

Deep-dive reference for the `figma-known-pitfalls` skill — extracted from the 'Pitfall 8: Polling Instead of Webhooks' step of the workflow.

**Problem:** Polling `GET /v1/files/:key` every 30 seconds wastes rate limit quota.

```typescript
// BAD -- 2,880 API calls per file per day
setInterval(async () => {
  const file = await figmaFetch(`/v1/files/${fileKey}`);
  if (file.version !== lastVersion) await sync();
}, 30_000);

// GOOD -- webhook notifies you only when file changes
// POST /v2/webhooks with event_type: "FILE_UPDATE"
// Result: ~10-50 calls/day instead of 2,880
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
