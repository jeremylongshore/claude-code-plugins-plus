---
name: supabase-security-basics
description: |
  Execute apply Supabase security best practices for secrets and access control.
  Use when securing API keys, implementing least privilege access,
  or auditing Supabase security configuration.
  Trigger with phrases like "supabase security", "supabase secrets",
  "secure supabase", "supabase API key security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Supabase Security Basics

## Prerequisites
- Supabase SDK installed
- Understanding of environment variables
- Access to Supabase dashboard


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Secure API key storage
- Environment-specific access controls
- Audit logging enabled

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Supabase Security Guide](https://supabase.com/docs/security)
- [Supabase API Scopes](https://supabase.com/docs/scopes)
