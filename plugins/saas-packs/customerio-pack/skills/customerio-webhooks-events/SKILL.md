---
name: customerio-webhooks-events
description: |
  Implement Customer.io webhook handling.
  Use when processing delivery events, handling callbacks,
  or integrating Customer.io event streams.
  Trigger with phrases like "customer.io webhook", "customer.io events",
  "customer.io callback", "customer.io delivery status".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io Webhooks & Events

## Overview
Implement webhook handling for Customer.io events including email delivery, opens, clicks, bounces, and data warehouse streaming.

## Prerequisites
- Public endpoint for webhooks
- Webhook signing secret from Customer.io
- Event processing infrastructure

## Instructions

### Step 1: Define Webhook Event Types
Create TypeScript interfaces for all webhook event types (email, push, SMS, in-app) with full payload typing.

### Step 2: Build Webhook Handler with Signature Verification
Implement HMAC-SHA256 signature verification using `crypto.timingSafeEqual` and event routing by metric type.

### Step 3: Set Up Express Router
Configure Express with raw body parsing for signature verification and route webhook requests to the handler.

### Step 4: Add Event Queue for Reliability
Use BullMQ with Redis to queue webhook events for reliable processing with retries and exponential backoff.

### Step 5: Integrate Reporting API
Query Customer.io's Reporting API for delivery metrics and campaign performance data.

### Step 6: Stream to Data Warehouse
Forward webhook events to BigQuery (or your data warehouse) for analytics and reporting.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Webhook event type definitions
- Signature verification handler
- Express router setup
- Event queue for reliability
- Reporting API integration
- Data warehouse streaming

## Error Handling
| Issue | Solution |
|-------|----------|
| Invalid signature | Verify webhook secret matches dashboard |
| Duplicate events | Use event_id for deduplication |
| Queue overflow | Increase worker concurrency |
| Missing events | Check endpoint availability and logs |

## Resources
- [Webhooks Documentation](https://customer.io/docs/webhooks/)
- [Reporting API](https://customer.io/docs/api/app/)

## Next Steps
After webhook setup, proceed to `customerio-performance-tuning` for optimization.

## Examples

**Basic usage**: Apply customerio webhooks events to a standard project setup with default configuration options.

**Advanced scenario**: Customize customerio webhooks events for production environments with multiple constraints and team-specific requirements.