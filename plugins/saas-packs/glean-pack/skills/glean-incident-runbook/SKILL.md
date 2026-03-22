---
name: glean-incident-runbook
description: |
  Triage: Is search returning results? Check Glean status page.
  Trigger: "glean incident runbook", "incident-runbook".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Incident Runbook

## Overview

Triage: Is search returning results? Check Glean status page. Is content stale? Check connector last successful run. Are permissions wrong? Verify datasource config with getdatasourceconfig. Is specific content missing? Check document ID with direct search. Escalate to Glean support with datasource name and error details.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
