---
name: groq-data-handling
description: |
  Use when you need to keep PII out of Groq API calls, filter model responses,
  audit-log conversations, or track token cost and usage for a Groq integration.
  Implements prompt sanitization, PII redaction, response filtering, and usage
  tracking. Trigger with phrases like "groq data", "groq PII", "groq GDPR",
  "groq data retention", "groq privacy", "groq compliance".
allowed-tools: Read, Write, Edit
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- compliance
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Data Handling

## Overview

Manage data flowing through Groq's inference API. This skill wires a privacy
pipeline around the Groq SDK: sanitize prompts before they are sent, filter
responses after they return, redact PII, hash-log an audit trail, and track
token usage and cost. Key fact: Groq does not use API data for model training
([Groq Privacy Policy](https://groq.com/privacy-policy/)).

## Prerequisites

- Node.js project with the `groq-sdk` package installed (`npm i groq-sdk`).
- A Groq API key exported as `GROQ_API_KEY`. The SDK reads it automatically
  from the environment — `new Groq()` needs no explicit argument. Never hardcode
  the key; keep it in an untracked `.env` or your secret manager.
- Node's built-in `crypto` module (for the audit hash) — no install needed.

## Instructions

The pipeline layers in four stages; drop simple add-ons (moderation, cost
reporting) on top. Each snippet below is the skeleton — the full, copy-ready
code for every stage is in [references/implementation.md](references/implementation.md).

1. **Sanitize input** — run a PII rule table over every message before it
   leaves your process, flagging which categories were caught:

   ```typescript
   function sanitizeMessages(messages: any[]): { messages: any[]; hadPII: boolean } {
     // apply PII_RULES to each message's content; return redacted copy + flag
   }
   ```

2. **Wrap the completion call** — call `safeCompletion(...)` instead of the raw
   `groq.chat.completions.create`, so input and response both pass the sanitizer.

3. **Track usage** — `trackUsage(model, completion.usage, sessionId)` records
   token counts and estimated cost per call using a per-model price table.

4. **Audit** — `auditedCompletion(...)` ties it together and logs a SHA-256
   hash of the prompt (never the prompt text) so the audit trail carries no
   sensitive content.

For content moderation via Llama Guard and a daily cost report, see
[references/examples.md](references/examples.md).

### Groq data policy

- Groq does **not** train on API request/response data.
- Prompts and completions are processed and discarded.
- Groq may temporarily log requests for abuse prevention.
- For enterprise: contact Groq for DPA and SOC 2 compliance details.

## Output

- **Sanitized messages/responses** — text with `[EMAIL]`, `[PHONE]`, `[SSN]`,
  `[CARD]`, `[IP]` placeholders swapped in for detected PII, plus a `hadPII`
  boolean and a list of redacted categories.
- **Usage records** — one JSON line per call (`type: "groq_usage"`) with model,
  token counts, and `estimatedCostUsd`.
- **Audit entries** — one JSON line per call (`type: "groq_audit"`) carrying a
  prompt hash, `piiDetected`, `responseFiltered`, and the usage record.
- **Cost report** — an aggregated object with `totalCost`, `totalTokens`,
  `totalCalls`, and a per-model breakdown (see the sample in
  [references/examples.md](references/examples.md)).

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| PII leaks in response | Model echoes sensitive input | Apply response filtering on all completions |
| Cost spike | 70B model for all requests | Route simple tasks to 8B |
| Missing usage data | Streaming mode | Use non-streaming for tracked requests, or estimate |
| Audit gaps | Not all code paths use wrapper | Lint rule: ban direct `groq.chat.completions.create` |
| `GROQ_API_KEY` not set | Key missing from environment | Export the key before running; the SDK throws on an unauthenticated call |

## Examples

- **Full four-stage pipeline** (sanitizer, safe wrapper, usage tracker,
  audited completion) — [references/implementation.md](references/implementation.md).
- **Content safety check** with Llama Guard and a **daily cost report** —
  [references/examples.md](references/examples.md).

Minimal end-to-end use once the helpers are in place:

```typescript
const { content, audit } = await auditedCompletion(sessionId, messages);
// content is PII-filtered; audit is a hash-only record safe to persist
```

## Resources

- [Groq Privacy Policy](https://groq.com/privacy-policy/)
- [Groq Pricing](https://groq.com/pricing)
- [Llama Guard (content moderation)](https://console.groq.com/docs/model/meta-llama/llama-guard-4-12b)
- [Full implementation](references/implementation.md) · [Examples](references/examples.md)

For enterprise access controls, see the `groq-enterprise-rbac` skill.
