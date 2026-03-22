---
name: glean-security-basics
description: |
  Token security: Indexing tokens have write access -- never expose in frontend.
  Trigger: "glean security basics", "security-basics".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, enterprise-search, glean]
compatible-with: claude-code
---

# Glean Security Basics

## Overview

Token security: Indexing tokens have write access -- never expose in frontend. Client tokens are user-scoped -- use with X-Glean-Auth-Type header. Rotate tokens quarterly via Admin > API Tokens. Document permissions: use allowedUsers/allowedGroups for sensitive content. SAML SSO for Glean web access. All API calls over HTTPS.

## Resources

- [Glean Developer Portal](https://developers.glean.com/)
- [Indexing API](https://developers.glean.com/api-info/indexing/getting-started/overview)
- [Search API](https://developers.glean.com/api/client-api/search/overview)
