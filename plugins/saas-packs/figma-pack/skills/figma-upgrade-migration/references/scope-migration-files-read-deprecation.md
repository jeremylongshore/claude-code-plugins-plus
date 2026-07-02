# Step 1: Scope Migration (files:read Deprecation)

Deep-dive reference for the `figma-upgrade-migration` skill — extracted from the 'Step 1: Scope Migration (files:read Deprecation)' step of the workflow.

The `files:read` scope is deprecated. Migrate to granular scopes:

| Deprecated Scope | Replacement Scopes | Endpoints Covered |
|-----------------|-------------------|-------------------|
| `files:read` | `file_content:read` | `GET /v1/files/:key`, `GET /v1/images/:key` |
| `files:read` | `file_comments:read` | `GET /v1/files/:key/comments` |
| `files:read` | `file_dev_resources:read` | `GET /v1/files/:key/dev_resources` |
| `files:read` | `file_versions:read` | `GET /v1/files/:key/versions` |

**Migration steps:**

1. Audit which endpoints your code calls
2. Map each endpoint to its required scope
3. Generate a new PAT with granular scopes
4. Update OAuth apps with new scope list
5. Test all endpoints with the new token
6. Revoke old tokens

```bash
# Find all Figma API calls in your codebase
grep -rn "api.figma.com" --include="*.ts" --include="*.js" src/ \
  | grep -oP '/v\d/[a-z_/]+' | sort -u

# Example output:
# /v1/files
# /v1/files/comments
# /v1/images
# /v2/webhooks
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
