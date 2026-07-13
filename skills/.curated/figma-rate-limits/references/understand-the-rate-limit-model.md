# Step 1: Understand the Rate Limit Model

Deep-dive reference for the `figma-rate-limits` skill — extracted from the 'Step 1: Understand the Rate Limit Model' step of the workflow.

**Endpoint tiers** (limits are per-user, per-minute):

| Tier | Endpoints | Typical Limit |
|------|-----------|--------------|
| Tier 1 | `GET /v1/files`, `GET /v1/images` | Higher quota |
| Tier 2 | `GET /v1/files/:key/comments`, `GET /v1/files/:key/variables/local` | Moderate quota |
| Tier 3 | `GET /v1/teams/:id/components`, `GET /v1/teams/:id/styles` | Lower quota |

**429 response headers:**

| Header | Type | Meaning |
|--------|------|---------|
| `Retry-After` | Integer (seconds) | Wait this long before retrying |
| `X-Figma-Plan-Tier` | String | Your Figma plan level |
| `X-Figma-Rate-Limit-Type` | String | `"low"` or `"high"` rate limit |
| `X-Figma-Upgrade-Link` | String | URL to upgrade for higher limits |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
