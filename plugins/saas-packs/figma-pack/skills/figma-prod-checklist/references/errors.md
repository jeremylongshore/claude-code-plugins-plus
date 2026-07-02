# figma-prod-checklist: Error Handling

Error reference for the `figma-prod-checklist` skill — extracted from the skill's Error Handling guidance.

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| Auth Failure | 403 errors > 0 | P1 | Rotate PAT immediately |
| Rate Limited | 429 errors > 5/min | P2 | Reduce request rate; check plan tier |
| High Latency | P95 > 5000ms | P2 | Check Figma status; add caching |
| API Down | 5xx errors > 10/min | P1 | Enable fallback; check status.figma.com |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
