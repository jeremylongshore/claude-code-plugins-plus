---
name: glean-enterprise-rbac
description: |
  Map AD/Okta groups to Glean document permissions using allowedGroups.
  Trigger: "glean enterprise rbac", "enterprise-rbac".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Enterprise Rbac

## Overview

Map AD/Okta groups to Glean document permissions using allowedGroups. Super Admins create indexing tokens. Regular admins manage datasources. Document permissions control search visibility per user. Use SAML SSO for Glean web access. Audit token usage and rotate quarterly.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
