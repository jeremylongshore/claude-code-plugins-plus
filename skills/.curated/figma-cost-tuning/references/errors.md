# figma-cost-tuning: Error Handling

Error reference for the `figma-cost-tuning` skill — extracted from the skill's Error Handling guidance.

| Issue | Cause | Solution |
|-------|-------|----------|
| Hitting rate limits often | No caching or batching | Implement caching + batch requests |
| Variables API 403 | Not on Enterprise plan | Use styles API (free on all plans) |
| High bandwidth costs | Fetching full file trees | Use `depth=1` and `/nodes` endpoint |
| Polling waste | No webhooks configured | Set up FILE_UPDATE webhook |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
