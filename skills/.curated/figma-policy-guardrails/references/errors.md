# figma-policy-guardrails: Error Handling

Error reference for the `figma-policy-guardrails` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| False positive on token scan | Test fixture contains figd_ | Exclude test fixtures directory |
| Policy blocks legitimate request | Too restrictive | Add exception list for specific paths |
| Startup validation fails | Missing env vars | Check deployment config |
| Audit log noise | Too many entries | Filter to write operations only |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
