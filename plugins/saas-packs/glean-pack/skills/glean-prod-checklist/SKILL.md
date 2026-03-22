---
name: glean-prod-checklist
description: |
  Pre-launch: All datasources indexed and searchable.
  Trigger: "glean prod checklist", "prod-checklist".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Prod Checklist

## Overview

Pre-launch: All datasources indexed and searchable. Document permissions tested with different user roles. Connector scheduled (daily cron or event-driven). Error alerting configured. Search quality validated with test queries. Token rotation procedure documented. Fallback plan if Glean is unavailable.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
