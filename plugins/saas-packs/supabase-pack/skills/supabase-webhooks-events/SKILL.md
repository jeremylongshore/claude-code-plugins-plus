---
name: supabase-webhooks-events
description: |
  Implement Supabase webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Supabase event notifications securely.
  Trigger with phrases like "supabase webhook", "supabase events",
  "supabase webhook signature", "handle supabase events", "supabase notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Supabase Webhooks Events

## Prerequisites
- Supabase webhook secret configured
- HTTPS endpoint accessible from internet
- Understanding of cryptographic signatures
- Redis or database for idempotency (optional)

## Instructions

### Step 1: Register Webhook Endpoint
Configure your webhook URL in the Supabase dashboard.

### Step 2: Implement Signature Verification
Use the signature verification code to validate incoming webhooks.

### Step 3: Handle Events
Implement handlers for each event type your application needs.

### Step 4: Add Idempotency
Prevent duplicate processing with event ID tracking.

## Output
- Secure webhook endpoint
- Signature validation enabled
- Event handlers implemented
- Replay attack protection active

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Supabase Webhooks Guide](https://supabase.com/docs/webhooks)
- [Webhook Security Best Practices](https://supabase.com/docs/webhooks/security)

## Overview

Implement Supabase webhook signature validation and event handling.