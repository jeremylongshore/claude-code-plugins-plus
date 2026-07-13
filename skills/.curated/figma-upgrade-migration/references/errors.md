# figma-upgrade-migration: Error Handling

Error reference for the `figma-upgrade-migration` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 after scope change | Missing required scope | Add the specific scope for each endpoint |
| Webhook not firing | V1 webhook still active | Delete V1, create V2 webhook |
| OAuth flow broken | Publishing flow not completed | Complete app publishing in dashboard |
| Token format mismatch | Old token type | Generate new PAT with `figd_` prefix |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
