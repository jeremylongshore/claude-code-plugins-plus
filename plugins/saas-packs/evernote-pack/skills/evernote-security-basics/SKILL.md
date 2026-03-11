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

1. See implementation guide for detailed steps.

2. For full implementation details and code examples, load:
3. `references/implementation-guide.md`

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

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with security |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply evernote security basics to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote security basics for production environments with multiple constraints and team-specific requirements.