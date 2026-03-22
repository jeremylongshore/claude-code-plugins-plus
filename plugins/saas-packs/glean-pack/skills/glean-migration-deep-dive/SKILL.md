---
name: glean-migration-deep-dive
description: |
  Migrate from Elasticsearch/Algolia: 1) Export all documents from source, 2) Transform to Glean document schema (id, title, url, body, permissions), 3) Create datasource with adddatasource, 4) Bulk index with bulkindexdocuments, 5) Validate search quality with test queries, 6) Switch search UI to use Glean Client API.
  Trigger: "glean migration deep dive", "migration-deep-dive".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Migration Deep Dive

## Overview

Migrate from Elasticsearch/Algolia: 1) Export all documents from source, 2) Transform to Glean document schema (id, title, url, body, permissions), 3) Create datasource with adddatasource, 4) Bulk index with bulkindexdocuments, 5) Validate search quality with test queries, 6) Switch search UI to use Glean Client API. Typical timeline: 2-4 weeks.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
