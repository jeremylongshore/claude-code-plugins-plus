---
name: posthog-webhooks-events
description: |
  Implement PostHog webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling PostHog event notifications securely.
  Trigger with phrases like "posthog webhook", "posthog events",
  "posthog webhook signature", "handle posthog events", "posthog notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# PostHog Webhooks & Events

## Overview

Handle PostHog webhooks triggered by Actions and event-based alerts. PostHog fires webhooks when defined Actions match incoming events, allowing you to send notifications, update external systems, or trigger workflows based on user behavior patterns.

## Prerequisites

- PostHog project with API access (cloud or self-hosted)
- PostHog project API key and personal API key
- HTTPS endpoint for receiving webhook deliveries
- Actions configured in PostHog dashboard

## Webhook Event Types

| Event Source | Trigger | Payload |
|-------------|---------|---------|
| Action webhook | Action matches event | Event properties, person data |
| Zapier integration | Action fires | Structured action data |
| HogQL alert | Query threshold exceeded | Alert details, query results |
| Feature flag change | Flag toggled | Flag key, rollout percentage |
| Export completed | Data export finishes | Export URL, row count |

## Instructions

### Step 1: Create an Action with Webhook

Use the PostHog API to create an Action that fires on specific events (e.g., autocapture on signup page). Configure the Action's steps with event type and URL matching.

### Step 2: Configure Webhook Endpoint

Build an Express endpoint at `/webhooks/posthog` that receives the event payload (event name, person data, properties, timestamp). Acknowledge with 200 immediately, then route to handlers.

### Step 3: Route and Handle Events

Implement a switch on event name to dispatch to specific handlers: `onUserSignup` (sync to CRM, Slack notify), `onSubscriptionUpgrade` (revenue tracking), `onFeatureActivated` (adoption tracking).

### Step 4: Query Events via API

Use the PostHog events API to query recent events by name and time range for reporting and analysis.

For complete TypeScript implementations, event handlers, and API query code, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not firing | Action not matched | Test Action with debug mode in PostHog |
| Missing person data | Anonymous user | Ensure `posthog.identify()` called first |
| Duplicate events | Action matches multiple | Refine Action event/URL filters |
| Rate limited | Too many API calls | Use batch endpoints for queries |

## Resources

- [PostHog Webhooks](https://posthog.com/docs/webhooks)
- [PostHog Actions](https://posthog.com/docs/data/actions)
- [PostHog API Reference](https://posthog.com/docs/api)

## Next Steps

For deployment setup, see `posthog-deploy-integration`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [PostHog implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Examples

**Basic usage**: Apply posthog webhooks events to a standard project setup with default configuration options.

**Advanced scenario**: Customize posthog webhooks events for production environments with multiple constraints and team-specific requirements.