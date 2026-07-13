# Step 1: Generate a Personal Access Token

Deep-dive reference for the `figma-install-auth` skill — extracted from the 'Step 1: Generate a Personal Access Token' step of the workflow.

1. Open Figma > Settings > Account > Personal access tokens
2. Click **Generate new token**
3. Name the token and assign scopes:

| Scope | Access | Use Case |
|-------|--------|----------|
| `file_content:read` | Read file JSON | Inspecting layers, extracting design tokens |
| `file_content:write` | Modify files | Programmatic design updates |
| `file_comments:read` | Read comments | Review tooling |
| `file_comments:write` | Post comments | Automated feedback |
| `file_dev_resources:read` | Dev resources | Dev mode integrations |
| `file_variables:read` | Read variables | Design token sync |
| `file_variables:write` | Write variables | Token pipeline |
| `webhooks:write` | Manage webhooks | Event-driven automation |

1. Copy the token immediately -- it is shown only once
2. PATs expire after a maximum of 90 days

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
