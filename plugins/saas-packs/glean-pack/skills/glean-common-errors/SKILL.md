---
name: glean-common-errors
description: |
  Diagnose and fix common Glean API errors including indexing failures, search issues, and permission problems.
  Trigger: "glean error", "glean not indexing", "glean search empty", "debug glean".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Common Errors

## Error Reference

### 401 Unauthorized
**Cause:** Invalid or expired API token.
**Fix:** Regenerate token in Admin > Settings > API Tokens.

### 403 Forbidden — Wrong Token Type
**Cause:** Using indexing token for search or vice versa.
**Fix:** Indexing API uses indexing tokens. Client API uses client tokens with `X-Glean-Auth-Type: BEARER`.

### No Search Results After Indexing
**Causes:** Documents still processing (1-5 min), permissions blocking, query doesn't match.
**Fix:** Wait 5 minutes. Check permissions allow the searching user. Broaden query.

### Bulk Index Upload Errors
| Error | Cause | Solution |
|-------|-------|----------|
| `uploadId already used` | Duplicate upload | Generate unique ID per run |
| `document too large` | Body > 100KB | Truncate or split content |
| `invalid datasource` | Datasource not created | Run `adddatasource` first |
| `missing required field` | No `id` or `title` | Ensure all documents have both |

### Permission Denied on Documents
**Cause:** Document `permissions` restrict visibility.
**Fix:** Set `allowAnonymousAccess: true` for public docs or add specific users/groups.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API Docs](https://developers.glean.com/api-info/indexing/getting-started/overview)
