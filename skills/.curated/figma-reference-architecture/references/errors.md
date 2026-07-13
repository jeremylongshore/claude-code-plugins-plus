# figma-reference-architecture: Error Handling

Error reference for the `figma-reference-architecture` skill — extracted from the skill's Error Handling guidance.

| Layer | Error | Recovery |
|-------|-------|----------|
| Client | 429 Rate Limited | Retry with `Retry-After` header |
| Client | 403 Forbidden | Alert on token expiry; fail gracefully |
| Cache | Cache miss storm | Stale-while-revalidate pattern |
| Webhook | Duplicate events | Idempotency via event timestamp |
| Export | Image render null | Skip node, log warning |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
