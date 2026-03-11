---
name: customerio-reference-architecture
description: |
  Implement Customer.io reference architecture.
  Use when designing integrations, planning architecture,
  or implementing enterprise patterns.
  Trigger with phrases like "customer.io architecture", "customer.io design",
  "customer.io enterprise", "customer.io integration pattern".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Customer.io Reference Architecture

## Overview
Enterprise-grade reference architecture for Customer.io integration with proper separation of concerns, event-driven processing, and infrastructure as code.

## Architecture Principles
1. **Separation of Concerns**: Track API, App API, and Webhooks handled by separate services
2. **Event-Driven**: Message queues for reliable async processing
3. **Idempotency**: All operations safely retryable
4. **Observability**: Events emitted for monitoring and debugging
5. **Infrastructure as Code**: All resources defined in Terraform

## Instructions

### Step 1: Build Core Service Layer
Create a `CustomerIOService` class extending EventEmitter with typed config, Track and App API clients, and lifecycle events for identify, track, and transactional operations.

### Step 2: Add Event Bus Integration
Implement Kafka-based event processing with topics for identify, track, and transactional operations, plus dead letter queue for failures.

### Step 3: Create Repository Pattern
Build a `UserMessagingRepository` that syncs user data from your database to Customer.io and manages messaging preferences.

### Step 4: Implement Webhook Handler
Create an EventEmitter-based webhook handler with signature verification, per-event-type listeners, and wildcard streaming to data warehouse.

### Step 5: Define Infrastructure as Code
Write Terraform for GCP Secret Manager secrets, Cloud Run service, Pub/Sub topics, and BigQuery tables for event analytics.

For detailed implementation code and Terraform configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Core Customer.io service layer with EventEmitter
- Kafka event bus integration with DLQ
- Repository pattern for user messaging
- Webhook handler with signature verification
- Terraform infrastructure definitions

## Error Handling
| Issue | Solution |
|-------|----------|
| Event processing failure | Routes to dead letter queue |
| Secret rotation needed | Update via Terraform + secrets manager |
| Webhook signature invalid | Verify secret matches dashboard |

## Resources
- [Customer.io API Reference](https://customer.io/docs/api/)
- [Webhook Documentation](https://customer.io/docs/webhooks/)

## Next Steps
After implementing architecture, proceed to `customerio-multi-env-setup` for multi-environment configuration.
