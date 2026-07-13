# figma-rate-limits: Error Handling

Error reference for the `figma-rate-limits` skill — extracted from the skill's Error Handling guidance.

| Scenario | Detection | Response |
|----------|-----------|----------|
| Single 429 | `Retry-After` header | Wait exactly that duration |
| Repeated 429s | Multiple retries exhausted | Log, alert, back off longer |
| `low` rate limit type | `X-Figma-Rate-Limit-Type: low` | Consider upgrading Figma plan |
| Batch too large | 400 Bad Request | Reduce batch size to 50 IDs |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
