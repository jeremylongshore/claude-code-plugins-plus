# Quick Reference

Supplemental reference for the `figma-known-pitfalls` skill — extracted from the skill's 'Quick Reference' section.

| # | Pitfall | Detection | Fix |
|---|---------|-----------|-----|
| 1 | Full file fetch | Response > 1MB | Use `depth=1` or `/nodes` |
| 2 | No rate limit handling | 429 errors | Read `Retry-After`, batch requests |
| 3 | Stale image URLs | Broken images after 30 days | Re-export or short TTL cache |
| 4 | Hardcoded PAT | `grep -r figd_` in source | Use `process.env.FIGMA_PAT` |
| 5 | Deprecated scope | `files:read` in token config | Use `file_content:read` |
| 6 | Wrong color format | Colors look wrong | Multiply by 255 |
| 7 | Null image render | TypeError on null URL | Filter null entries |
| 8 | Polling loop | High API call volume | Use Webhooks V2 |
| 9 | SVG with scale | Scale parameter ignored | SVG is always 1x |
| 10 | No webhook verification | Security vulnerability | Verify passcode |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
