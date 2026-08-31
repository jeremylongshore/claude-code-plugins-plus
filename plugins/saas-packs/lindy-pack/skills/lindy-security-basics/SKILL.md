---
name: lindy-security-basics
description: 'Implement security best practices for Lindy agents and integrations.

  Use when securing webhook secrets, scoping connected accounts,

  controlling side effects, or auditing agent access.

  Trigger with phrases like "lindy security", "secure lindy",

  "lindy webhook security", "lindy permissions", "lindy audit".

  '
allowed-tools: Read, Write, Edit
version: 1.19.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lindy
- api
- security
compatibility: Designed for Claude Code
---
# Lindy Security Basics

## Overview

Secure Lindy workflows at the boundaries Lindy currently documents: generated
Webhook Received secrets, per-action connected-account selection, target-service
authentication in HTTP Request, Ask for Confirmation/draft modes, dedicated Computer
Use sessions, Tasks, and Test Panel. Do not rely on an undocumented Lindy API key,
webhook signature, role, connection-sharing level, fixed quota, or plan entitlement.

## Prerequisites

- Lindy workspace with an editable custom agent
- Inventory of triggers, actions, connected accounts, external endpoints, data
  classes, owners, and consequential side effects
- Sanitized fixtures and test/sandbox integrations

## Instructions

### Step 1: Draw the Trust Map

For every path, record source, destination, data fields, credential owner, selected
connected account, allowed side effects, approver, failure path, and evidence source.
Separate these directions:

| Direction | Supported boundary |
|---|---|
| Application to Lindy | Webhook Received URL + Lindy-generated bearer secret |
| Lindy to external service | HTTP Request + that service's authentication |
| External account action | Exactly the connected account selected on the action |
| Lindy callback to application | Receiver-owned trust boundary; no documented Lindy signature claim |

### Step 2: Secure Webhook Received

1. Create the webhook inside the Webhook Received trigger.
2. Generate the secret, copy it once, and store it in the caller's secret manager.
3. Send it only in the Authorization bearer header to the generated HTTPS URL.
4. Keep the webhook URL/secret out of prompts, bodies, query strings, task titles,
   screenshots, logs, and tickets.
5. Minimize and validate the caller's payload before transmission.
6. Rotate after suspected exposure by creating/reconfiguring the protected boundary,
   verifying the replacement, and retiring the old value according to the current UI.

The bearer secret authenticates the caller **to Lindy**. It does not authenticate a
callback from Lindy to your application, and Lindy's Webhooks guide does not document
an HMAC signature or timestamp header for that callback.

### Step 3: Scope Connected Accounts and Actions

Lindy documents that each action selects one connected account. For every action:

- select the account with the minimum data and authority required;
- prefer a dedicated work/test account when the integration supports one;
- remove actions and connections no longer required by the workflow;
- avoid combining broad read and consequential write abilities in an autonomous
  Agent Step when deterministic actions/conditions are sufficient; and
- use a dedicated Computer for an agent that needs Computer Use so saved sessions and
  site credentials are not shared across unrelated work.

Do not invent local permission dictionaries or quotas and describe them as Lindy
controls. Enforce application-owned authorization again at any external receiver.

### Step 4: Put Humans Before Consequential Side Effects

Enable **Ask for Confirmation** on supported actions that send messages, update
records, create events, or cause other consequential effects. Use draft mode where
available. Add condition-based escalation for unknown/out-of-scope cases. Keep
confirmation enabled until representative testing and review justify a deliberate
change; money, contracts, access changes, deletion, and sensitive external
communications should retain explicit approval.

### Step 5: Minimize Data Across Every Step

- Use stable references instead of full messages/documents where possible.
- Do not pass all webhook headers or the entire body to later actions.
- Send HTTP Request only fields required by the target schema.
- Bound lengths, collection sizes, nesting, and allowed enum values.
- Never print secrets or sensitive inputs in Run Code; stdout becomes `text`.
- Keep task links restricted because Tasks can expose step inputs and outputs.
- Redact incident/evaluation exports; retain details only in approved systems.

Prompt instructions are defense in depth, not authorization. Conditions, selected
accounts, receiver-side checks, confirmation, and schema validation must enforce the
boundary even if model output is incorrect or adversarial.

### Step 6: Test Fail-Closed Behavior

Use synthetic data and test accounts. Lindy's Test Panel executes real actions.
Verify valid flow plus wrong/missing webhook secret, oversized/unknown payload,
unexpected outbound host, target 401/403/429/5xx, malformed response, attempted prompt
injection, missing approval, and untrusted callback content. Each negative case must
stop, quarantine, or request human review without completing its side effect.

### Step 7: Review Tasks and Current Account Controls

Use Tasks to inspect the exact step order, selected paths, inputs/outputs, errors, and
timestamps after testing and deployment. Review connected accounts and agent actions
on a defined owner-approved cadence. For organization identity, audit, compliance,
or contractual controls, verify current availability and configuration in Lindy's
official security/pricing material and your workspace; do not freeze plan claims in
this skill.

## Security Checklist

- [ ] Trust map covers every inbound, outbound, connected-account, and callback path
- [ ] Webhook Received uses the generated bearer secret and exact generated URL
- [ ] Secrets are distinct, nonempty, protected, and absent from content/logs
- [ ] Every action uses the minimum-authority connected account
- [ ] Consequential side effects require confirmation/draft/review
- [ ] Payloads and Run Code inputs/outputs have explicit schemas and bounds
- [ ] Callback content is untrusted until receiver-owned checks succeed
- [ ] Test Panel uses synthetic data and test integrations
- [ ] Negative tests prove fail-closed behavior
- [ ] Tasks and connection/action inventory have owners and a review cadence

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Wrong caller reaches webhook | Missing/wrong generated bearer | Reject; rotate if exposure is suspected |
| Agent uses wrong account | Wrong account selected on action | Stop workflow and correct the explicit selection |
| Callback has no trusted auth boundary | Assumed Lindy signature | Quarantine; implement receiver-owned auth without claiming platform signing |
| Sensitive data appears in Tasks/logs | Payload/output too broad | Disable path, redact downstream copies, minimize schema, retest |
| Side effect runs during test | Production connection/no confirmation | Contain impact, restore state, use test account and confirmation |
| External receiver accepts excess authority | Lindy prompt treated as authorization | Enforce identity, schema, and authorization at receiver |

## Output

Return a security review containing:

- trust map and data classification for each boundary;
- credential inventory with owner, storage, rotation trigger, and separation proof;
- action-to-connected-account and side-effect inventory;
- confirmation/draft/escalation decisions;
- exact schema/data-minimization controls;
- happy-path and negative fail-closed test receipts; and
- open risks with owner and remediation, without copying secrets or sensitive payloads.

## Examples

For an inbound document event, the caller sends only a synthetic document reference
to the generated Webhook Received URL using its generated bearer secret. The workflow
uses a specifically selected read-only source account, transforms only the reference,
and stages any external update behind Ask for Confirmation. A separate application
receiver validates its own credential and minimal callback schema; it does not assume
an undocumented Lindy signature or act on callback text alone.

## Resources

- [Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [HTTP Request](https://docs.lindy.ai/skills/by-lindy/http-request)
- [Actions and account selection](https://docs.lindy.ai/fundamentals/lindy-101/actions)
- [Human in Loop](https://docs.lindy.ai/testing/human-in-the-loop)
- [Computer Use](https://docs.lindy.ai/skills/by-lindy/computer-use)
- [Test Panel](https://docs.lindy.ai/testing/test-panel)
- [Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)
- [Lindy Security](https://www.lindy.ai/security)

## Next Steps

Carry the completed trust map, negative-test receipts, and open risks into
`lindy-prod-checklist`; production readiness is not proven by this checklist alone.
