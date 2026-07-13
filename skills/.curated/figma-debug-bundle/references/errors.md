# figma-debug-bundle: Error Handling

Error reference for the `figma-debug-bundle` skill — extracted from the skill's Error Handling guidance.

| Item | What It Catches | Why It Matters |
|------|----------------|----------------|
| `/v1/me` response code | Token validity | 403 = expired/invalid PAT |
| `/v1/files` response code | File access | 404 = wrong key, 403 = not shared |
| Rate limit headers | Throttling state | `Retry-After` shows if currently limited |
| Response time | Latency issues | >2s suggests network or server problems |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
