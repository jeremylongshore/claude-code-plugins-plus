# Step 1: Understand Plan-Based Rate Limits

Deep-dive reference for the `figma-cost-tuning` skill — extracted from the 'Step 1: Understand Plan-Based Rate Limits' step of the workflow.

Figma rate limits vary by plan tier and seat type:

| Plan | Seat Types | Rate Limit Tier | Variables API |
|------|------------|----------------|---------------|
| Starter (Free) | Free | Lowest | No |
| Professional | Full, Viewer | Standard | No |
| Organization | Full, Collab, Viewer | Higher | No |
| Enterprise | Full, Collab, Viewer | Highest | Yes |

Key facts:

- Rate limits are per-user, per-minute
- View and Collab seats have lower limits than Full seats
- The Variables API (`/v1/files/:key/variables/*`) requires Enterprise
- Endpoint tiers (1/2/3) have different quotas within each plan

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
