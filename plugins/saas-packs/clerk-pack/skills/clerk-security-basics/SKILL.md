---
name: clerk-security-basics
description: |
  Implement security best practices with Clerk authentication.
  Use when securing your application, reviewing auth implementation,
  or hardening Clerk configuration.
  Trigger with phrases like "clerk security", "secure clerk",
  "clerk best practices", "clerk hardening".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Clerk Security Basics

## Overview
Implement security best practices for Clerk authentication in your application.

## Prerequisites
- Clerk SDK installed and configured
- Understanding of authentication security concepts
- Production deployment planned or active

## Instructions
- Step 1: Secure Environment Variables
- Step 2: Secure Middleware Configuration
- Step 3: Secure API Routes
- Step 4: Secure Webhook Handling
- Step 5: Session Security

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Secure environment configuration
- Hardened middleware
- Protected API routes
- Verified webhook handling

## Resources
- [Clerk Security](https://clerk.com/docs/security/overview)
- [Webhook Security](https://clerk.com/docs/integrations/webhooks/sync-data)
- [OWASP Guidelines](https://owasp.org/www-project-web-security-testing-guide/)

## Next Steps
Proceed to `clerk-prod-checklist` for production readiness.
