# figma-load-scale: Error Handling

Error reference for the `figma-load-scale` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| All requests 429'd | Rate too aggressive | Start lower, ramp gradually |
| Inconsistent limits | Shared rate limit bucket | Other services using same token |
| k6 connection errors | Too many parallel VUs | Reduce `preAllocatedVUs` |
| Results vary between runs | Leaky bucket state | Wait 5min between test runs |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
