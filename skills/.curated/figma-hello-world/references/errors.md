# figma-hello-world: Error Handling

Error reference for the `figma-hello-world` skill — extracted from the skill's Error Handling guidance.

| Error | Status | Cause | Solution |
|-------|--------|-------|----------|
| `Not found` | 404 | Invalid file key | Verify the key from the Figma URL |
| `Forbidden` | 403 | No access to file | Check token scopes and file permissions |
| `Rate limited` | 429 | Too many requests | Honor `Retry-After` header |
| Empty `document` | 200 | File has no pages | Check if file was recently created |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
