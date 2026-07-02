# figma-core-workflow-b: Error Handling

Error reference for the `figma-core-workflow-b` skill — extracted from the skill's Error Handling guidance.

| Error | Cause | Solution |
|-------|-------|----------|
| `null` in images map | Node is invisible or has 0% opacity | Make node visible in Figma |
| 400 Bad Request | Invalid node ID format | Use `pageId:nodeId` format (e.g., `0:1`) |
| 429 Rate Limited | Images endpoint is Tier 1 | Batch requests, honor `Retry-After` |
| Image URL expired | URLs expire after 30 days | Re-export; do not cache URLs long-term |
| SVG has `scale` > 1 | SVG ignores scale param | SVG always exports at 1x |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
