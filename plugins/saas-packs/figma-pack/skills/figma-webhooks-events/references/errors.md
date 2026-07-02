# figma-webhooks-events: Error Handling

Error reference for the `figma-webhooks-events` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not firing | Endpoint not HTTPS | Figma requires TLS |
| Invalid passcode | Wrong secret configured | Verify passcode in webhook creation |
| Webhook status PAUSED | Too many delivery failures | Fix endpoint, then recreate webhook |
| Missing `triggered_by` | Older event format | Check webhook V2 vs V1 |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
