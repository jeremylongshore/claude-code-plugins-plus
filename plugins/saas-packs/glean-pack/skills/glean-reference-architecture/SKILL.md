---
name: glean-reference-architecture
description: |
  Enterprise architecture: Source Systems -> Connectors (Cloud Run/Lambda, event-driven or scheduled) -> Glean Indexing API -> Glean Search Index -> Client API (Search + Chat) -> Your Apps (Slack bot, portal, internal tools).
  Trigger: "glean reference architecture", "reference-architecture".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Reference Architecture

## Overview

Enterprise architecture: Source Systems -> Connectors (Cloud Run/Lambda, event-driven or scheduled) -> Glean Indexing API -> Glean Search Index -> Client API (Search + Chat) -> Your Apps (Slack bot, portal, internal tools). Key decisions: incremental vs bulk indexing, permission model (open vs ACL), connector hosting (serverless vs always-on).

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
