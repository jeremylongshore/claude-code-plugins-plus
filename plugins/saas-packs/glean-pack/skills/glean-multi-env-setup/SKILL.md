---
name: glean-multi-env-setup
description: |
  Use separate datasource names per environment (wiki_staging vs wiki_prod).
  Trigger: "glean multi env setup", "multi-env-setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Multi Env Setup

## Overview

Use separate datasource names per environment (wiki_staging vs wiki_prod). Separate API tokens per environment. Never index production user data in staging. Use CI/CD with environment-specific secrets. Test search quality in staging before promoting connector changes.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
