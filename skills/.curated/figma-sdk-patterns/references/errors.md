# figma-sdk-patterns: Error Handling

Error reference for the `figma-sdk-patterns` skill — extracted from the skill's Error Handling guidance.

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Typed errors | `catch (e) { if (e instanceof FigmaRateLimitError) }` | Targeted recovery |
| Node walker | Traversing arbitrarily deep trees | Handles any file structure |
| Retry wrapper | Transient 429/5xx errors | Automatic recovery |
| Singleton | Shared client across modules | Consistent config, one token |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
