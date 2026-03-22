---
name: retellai-common-errors
description: |
  Diagnose and fix Retell AI voice agent errors: call failures, webhook issues, voice quality.
  Use when encountering Retell AI errors, debugging call issues, or troubleshooting agents.
  Trigger with phrases like "retell error", "call failed", "voice agent not working", "retell debug".
allowed-tools: Read, Grep, Bash(curl:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, retellai, voice, telephony, debugging]
compatible-with: claude-code, codex, openclaw
---

# Retell AI Common Errors

## Overview
Quick reference for the top Retell AI errors and their solutions.

## Prerequisites
- `retell-sdk` installed
- API key configured

## Instructions

### Error 1: 401 Unauthorized
```
RetellError: 401 — Invalid API key
```
**Fix:** Verify API key in Retell Dashboard. Ensure `RETELL_API_KEY` starts with `key_`.

### Error 2: Call Fails Immediately
```
RetellError: 400 — Invalid phone number format
```
**Fix:** Use E.164 format: `+14155551234`. Both `from_number` and `to_number` must be valid.

### Error 3: Agent Not Responding
```
Call connected but agent says nothing
```
**Fix:** Check LLM configuration:
```typescript
const llm = await retell.llm.retrieve(agent.response_engine.llm_id);
console.log(`Model: ${llm.model}`);
console.log(`Prompt length: ${llm.general_prompt.length} chars`);
// Ensure general_prompt is not empty and gives clear instructions
```

### Error 4: Function Call Timeout
```
Function call to https://your-api.com/endpoint timed out
```
**Fix:** Your function endpoint must respond within 5 seconds. Offload heavy work:
```typescript
app.post('/functions/lookup', async (req, res) => {
  // Respond immediately with acknowledgment
  const result = await quickLookup(req.body.args);
  res.json({ result: `Found: ${result.name}` });
  // Do NOT run async work before responding
});
```

### Error 5: Webhook Not Receiving Events
```
No webhook events received after call
```
**Fix:** Set `webhook_url` on the agent, not just in Dashboard settings:
```typescript
await retell.agent.update(agentId, {
  webhook_url: 'https://your-app.com/webhooks/retell',
});
```

### Error 6: Voice Quality Issues
```
Agent voice sounds robotic/choppy
```
**Fix:** Check network latency to Retell servers. Use a voice optimized for your use case. Try different voice IDs.

## Output
- Error identified and root cause found
- Fix applied and verified
- Call successfully completed

## Error Handling
| HTTP Code | Meaning | Retryable |
|-----------|---------|-----------|
| 400 | Bad request | No — fix params |
| 401 | Invalid API key | No — fix key |
| 404 | Agent/call not found | No — fix ID |
| 429 | Rate limited | Yes — backoff |
| 500+ | Server error | Yes — retry |

## Resources
- [Retell AI Documentation](https://docs.retellai.com)
- [retell-sdk npm](https://www.npmjs.com/package/retell-sdk)

## Next Steps
For debugging, see `retellai-debug-bundle`.
