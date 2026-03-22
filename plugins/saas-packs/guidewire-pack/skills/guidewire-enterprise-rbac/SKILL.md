---
name: guidewire-enterprise-rbac
description: |
  Implement Guidewire RBAC: API roles, user permissions, and security policies.
  Trigger: "guidewire enterprise rbac", "enterprise-rbac".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Enterprise Rbac

## Overview

GCC > Identity & Access: API roles define endpoint access (read/write per resource). User roles in InsuranceSuite control UI and business logic access. Security policies enforce data visibility. Map AD groups to Guidewire roles via SAML assertions.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
