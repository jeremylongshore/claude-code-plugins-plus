# figma-security-basics: Error Handling

Error reference for the `figma-security-basics` skill — extracted from the skill's Error Handling guidance.

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Token in git history | `git log -p \| grep figd_` | Revoke immediately, rotate, use BFG Repo Cleaner |
| Expired PAT | 403 errors in production | Set calendar reminder for 80-day mark |
| Over-scoped token | Audit in Figma Settings | Regenerate with minimum scopes |
| Webhook spoofing | Missing passcode check | Always verify passcode before processing |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
