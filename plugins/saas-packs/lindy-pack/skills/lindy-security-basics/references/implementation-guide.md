# Lindy Security Basics - Implementation Guide

## Direction Matters

The documented Webhook Received secret protects calls **from an application into
Lindy**. The caller places the Lindy-generated value in the Authorization bearer
header sent to the generated webhook URL. It is not a callback-verification secret,
and the public Webhooks guide does not document callback signing or timestamp headers.

For calls **from Lindy to an application**, use HTTP Request and the authentication
scheme owned by that application. For Send POST Request to Callback, do not assume a
platform signature; receive into an application-owned trust boundary and treat the
content as untrusted until its schema and authorization checks pass.

## Trust-Map Template

| Path | Source | Destination | Minimal fields | Credential owner | Side effect | Approval | Evidence |
|---|---|---|---|---|---|---|---|
| Inbound trigger | Application | Webhook Received | Event enum + stable reference | Lindy-generated secret stored by caller | Create task | N/A | Application receipt + Tasks |
| Outbound request | Lindy | Application endpoint | Explicit result schema | Target application | Defined by endpoint | Confirmation when consequential | Task + receiver audit metadata |
| Connected action | Lindy | Selected account | Required action fields | Integration/account owner | Send/update/create/etc. | Ask for Confirmation/draft | Task history |
| Callback | Lindy | Application receiver | Stable reference + bounded status | Receiver/application | Stage only | Validate before action | Receiver receipt |

## Review Procedure

1. Inventory every trigger, action, Agent Step skill, Run Code block, connected
   account, Computer, HTTP host, and callback URL.
2. Mark the fields that cross each edge and remove everything not required.
3. Confirm the credential belongs to that edge and is not reused elsewhere.
4. Confirm each action explicitly selects the intended connected account.
5. Put Ask for Confirmation or draft mode before consequential actions.
6. Add conditions for unknown/out-of-scope input and a fail-closed error route.
7. Save a known-good version, then run positive and negative synthetic tests.
8. Review Tasks and receiver-side audit metadata; do not export task content.

## Negative-Test Matrix

| Test | Required result |
|---|---|
| Missing/wrong Webhook Received bearer | Rejected; no trusted result |
| Body has extra field or exceeds bounds | Refused before or at boundary |
| HTTP Request host differs from allowlist | Refused; no credential sent |
| Target returns unauthorized/forbidden/rate-limit/server error | Error route; no partial side effect |
| Prompt asks to reveal a secret or broaden scope | Refusal/escalation; secret remains absent |
| Consequential action lacks approval | Test fails review; confirmation restored |
| Callback has unknown field/reference | Quarantined; no downstream action |
| Computer exposes unrelated saved session | Use dedicated Computer; repeat test |

## Evidence Rules

Receipts may contain agent/workflow key, test-case key, timestamp, outcome, HTTP
status class, selected account alias, approver decision, and task link with restricted
access. Receipts must not contain webhook URLs, bearer values, authorization headers,
customer content, prompts, block outputs, personal identifiers, or full error bodies.

## Official References

- [Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [HTTP Request](https://docs.lindy.ai/skills/by-lindy/http-request)
- [Actions and account selection](https://docs.lindy.ai/fundamentals/lindy-101/actions)
- [Human in Loop](https://docs.lindy.ai/testing/human-in-the-loop)
- [Computer Use](https://docs.lindy.ai/skills/by-lindy/computer-use)
- [Test Panel](https://docs.lindy.ai/testing/test-panel)
- [Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)
