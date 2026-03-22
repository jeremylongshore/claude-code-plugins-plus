---
name: guidewire-security-basics
description: |
  Implement Guidewire security: OAuth2 JWT, API roles, Gosu secure coding, and data protection.
  Trigger: "guidewire security basics", "security-basics".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Security Basics

## Overview

OAuth2 with short-lived JWTs, API roles in GCC (assign per-endpoint permissions), Gosu security: use gw.api.system.server.ServerUtil for auth, never hardcode credentials in Gosu, encrypt PII in custom entities. SAML SSO for Jutro frontends.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
