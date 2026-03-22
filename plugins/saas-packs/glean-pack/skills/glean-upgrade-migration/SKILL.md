---
name: glean-upgrade-migration
description: |
  Check Glean developer changelog for API changes.
  Trigger: "glean upgrade migration", "upgrade-migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Upgrade Migration

## Overview

Check Glean developer changelog for API changes. Test connector against staging environment. Update SDK/client packages. Verify document schema compatibility (new required fields?). Run search quality tests. Deploy updated connector. Monitor indexing errors post-deploy.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
