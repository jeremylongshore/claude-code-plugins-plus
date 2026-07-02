# figma-performance-tuning: Error Handling

Error reference for the `figma-performance-tuning` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| Stale cache | No invalidation | Use webhooks to invalidate on changes |
| Out of memory | Caching full file JSON | Use `depth=1` or `nodes` endpoint |
| Slow image exports | Large batch, high scale | Reduce scale; batch in groups of 50 |
| Expired image URLs | Cached URL older than 30 days | Set image cache TTL to <24h |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
