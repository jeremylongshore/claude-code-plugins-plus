---
name: evernote-security-basics
description: |
  Implement security best practices for Evernote integrations.
  Use when securing API credentials, implementing OAuth securely,
  or hardening Evernote integrations.
  Trigger with phrases like "evernote security", "secure evernote",
  "evernote credentials", "evernote oauth security".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Evernote Security Basics

## Overview
Security best practices for Evernote API integrations, covering credential management, OAuth implementation, data protection, and secure coding patterns.

## Prerequisites
- Evernote SDK setup
- Understanding of OAuth 1.0a
- Basic security concepts

## Instructions

See implementation guide for detailed steps.

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Secure credential management
- CSRF-protected OAuth flow
- Encrypted token storage
- Input validation utilities
- Secure logging with data redaction
- Token lifecycle management

## Resources
- [OAuth Documentation](https://dev.evernote.com/doc/articles/authentication.php)
- [API Key Permissions](https://dev.evernote.com/doc/articles/permissions.php)
- [OWASP Security Guidelines](https://owasp.org/www-project-web-security-testing-guide/)

## Next Steps
For production deployment checklist, see `evernote-prod-checklist`.
