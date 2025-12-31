# vercel-webhooks-events

## Skill Scaffold

```
vercel-webhooks-events/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement webhook signature validation, event handling, and replay protection for Vercel notifications.
**Workflow:** Used when implementing event-driven integrations that respond to Vercel notifications.
**Relates to:** Security builds on vercel-security-basics; leads to vercel-performance-tuning for optimization

## Summary

This skill covers secure webhook implementation for Vercel events. It includes Express.js endpoint setup with raw body parsing for signature verification, HMAC-SHA256 signature validation with timing-safe comparison, timestamp verification to prevent replay attacks, typed event handlers for different event types, and Redis-based idempotency to prevent duplicate processing. Local testing with ngrok and Vercel dev is also covered.
