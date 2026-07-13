# Step 1: Identify the Error Category

Deep-dive reference for the `figma-common-errors` skill — extracted from the 'Step 1: Identify the Error Category' step of the workflow.

## REST API HTTP Errors

| Status | Error | Cause | Solution |
|--------|-------|-------|----------|
| 400 | Bad Request | Malformed request, invalid node IDs | Verify node ID format (`pageId:nodeId`, e.g., `0:1`) |
| 403 | Forbidden | Invalid token, wrong scopes, no file access | Regenerate PAT with correct scopes; verify file sharing |
| 404 | Not Found | Wrong file key, deleted file, wrong endpoint | Check file key from URL; verify file exists |
| 429 | Rate Limited | Too many requests | Read `Retry-After` header; implement backoff |
| 500 | Internal Server Error | Figma server issue | Retry with exponential backoff; check status.figma.com |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
