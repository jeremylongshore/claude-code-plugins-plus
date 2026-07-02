# figma-reliability-patterns: Error Handling

Error reference for the `figma-reliability-patterns` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit stays open | Threshold too low | Increase threshold or decrease reset time |
| Stale fallback data | Cache not refreshed | Refresh cache on successful calls |
| Retry loops | Not respecting Retry-After | Always use the header value |
| Timeout too short | Large file responses | Increase timeout for `/v1/files` calls |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
