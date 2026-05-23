# oraclecloud-webhooks-events — One-Pager

Wire up event-driven workflows with OCI Events, Notifications (ONS), and Functions.

## The Problem

OCI Events + Notifications + Functions is the serverless stack, but event rule syntax is poorly documented, ONS topic limits are easy to hit, and Functions cold starts are brutal. Teams spend hours debugging why rules don't fire (malformed condition JSON), why subscriptions stay in "Pending" state (unconfirmed HTTPS endpoints), and which exact `eventType` strings to use. This wires up reliable event-driven workflows.

## The Solution

This skill provides the complete event-driven pipeline: creating ONS topics with confirmed subscriptions, writing Events rules with correct condition JSON syntax, a reference table of common event types (compute lifecycle, storage changes, audit events), and routing events to Functions for complex processing. Includes CLI and Python SDK examples for every step.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Platform engineers and DevOps teams building automated responses to OCI resource changes |
| **What** | Working event rules, ONS topics with subscriptions, and optional Function invocations triggered by resource state changes |
| **When** | Setting up alerting for instance lifecycle, automating responses to storage events, or routing audit events to external systems |

## Key Features

1. **ONS topic and subscription setup** — Create topics and subscribe HTTPS, email, or PagerDuty endpoints with confirmation handling
2. **Event rule condition syntax** — Correct JSON condition format with exact eventType strings for compute, storage, identity, and audit events
3. **Functions integration** — Route events to OCI Functions for complex processing beyond simple notifications

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
