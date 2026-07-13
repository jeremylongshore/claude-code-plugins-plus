# Step 2: Least-Privilege Scopes

Deep-dive reference for the `figma-security-basics` skill — extracted from the 'Step 2: Least-Privilege Scopes' step of the workflow.

Assign the minimum scopes needed for each use case:

| Use Case | Required Scopes |
|----------|----------------|
| Read file structure | `file_content:read` |
| Export images | `file_content:read` |
| Post comments | `file_comments:write` |
| Read variables (Enterprise) | `file_variables:read` |
| Manage webhooks | `webhooks:write` |
| Read team components | `team_library_content:read` |
| Dev mode resources | `file_dev_resources:read` |

**Deprecated scope:** `files:read` is deprecated. Use specific scopes like `file_content:read`, `file_comments:read` instead.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
