# navan-webhooks-events — One-Pager

Configure webhook listeners for real-time Navan booking, expense, and travel disruption notifications.

## The Problem

Navan generates critical travel events — new bookings, expense approvals, itinerary changes, travel disruptions — but without webhooks, teams resort to polling the REST API on timers. This wastes API quota, introduces latency, and misses time-sensitive events like flight cancellations that require immediate rebooking.

## The Solution

This skill sets up webhook callback endpoints that receive real-time event payloads from Navan. It covers registering callback URLs via the API, verifying payload signatures to prevent spoofing, and handling the key event types (booking created, expense submitted, trip disrupted) with proper acknowledgment and retry logic.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend developers building travel automation, expense workflow triggers, or disruption alerting systems |
| **What** | Webhook endpoint setup, signature verification, event routing, and retry-safe handler patterns |
| **When** | Adding real-time notifications to a Navan integration, building approval automation, or setting up travel disruption alerts |

## Key Features

1. **Event type routing** — Handle booking, expense, approval, and disruption events with typed payload parsing
2. **Signature verification** — HMAC-based payload validation to reject spoofed or tampered webhook calls
3. **Idempotent processing** — Deduplicate retried events using event IDs to prevent double-processing

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
