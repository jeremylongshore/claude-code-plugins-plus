---
name: glean-observability
description: |
  Track: documents indexed per run (total + new + updated + deleted), indexing errors and retries, search API latency, zero-result query rate, stale content age distribution.
  Trigger: "glean observability", "observability".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Observability

## Overview

Track: documents indexed per run (total + new + updated + deleted), indexing errors and retries, search API latency, zero-result query rate, stale content age distribution. Export metrics to Datadog/Prometheus. Alert on: indexing job failures, >10% error rate, stale content >30 days.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
