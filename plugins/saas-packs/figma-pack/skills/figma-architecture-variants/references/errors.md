# figma-architecture-variants: Error Handling

Error reference for the `figma-architecture-variants` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| CLI too slow | Full file fetch | Use `depth=1` and `/nodes` |
| Webhook not firing | No HTTPS | Deploy to platform with TLS |
| Plugin sandbox limits | Heavy computation | Offload to REST API via fetch in UI iframe |
| Wrong variant choice | Over-engineering | Start with CLI, add webhook when needed |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
