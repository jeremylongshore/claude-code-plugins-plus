---
name: glean-data-handling
description: |
  PII filtering: strip emails, phone numbers, SSNs from document body before indexing.
  Trigger: "glean data handling", "data-handling".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Data Handling

## Overview

PII filtering: strip emails, phone numbers, SSNs from document body before indexing. Document classification: use permissions.allowedUsers for confidential content, allowAnonymousAccess for public. Retention: delete documents older than policy threshold. Audit: log all indexed document IDs for compliance.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
