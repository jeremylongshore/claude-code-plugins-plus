---
name: glean-rate-limits
description: |
  Glean Indexing API: ~100 requests/min per token.
  Trigger: "glean rate limits", "rate-limits".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Rate Limits

## Overview

Glean Indexing API: ~100 requests/min per token. Bulk indexing: batches of 100 documents. Client API: ~60 searches/min per token. Implement exponential backoff on 429 responses. Use p-queue with concurrency=3 for indexing. For large corpora (>100K docs), use bulkindexdocuments over multiple hours.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
