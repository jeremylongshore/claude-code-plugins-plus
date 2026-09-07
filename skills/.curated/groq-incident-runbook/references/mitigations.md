# Immediate Mitigations

Apply the mitigation that matches the failure class identified in [triage-and-diagnostics.md](triage-and-diagnostics.md).

## Enable Fallback to Different Model

```typescript
// If primary model is failing, route to fallback
async function mitigateModelFailure(messages: any[]) {
  const models = [
    "llama-3.3-70b-versatile",  // Primary
    "llama-3.3-70b-specdec",    // Same quality, different infra
    "llama-3.1-8b-instant",     // Fastest, most available
  ];

  for (const model of models) {
    try {
      return await groq.chat.completions.create({
        model,
        messages,
        max_tokens: 1024,
        timeout: 10_000,
      });
    } catch (err: any) {
      console.warn(`Model ${model} failed: ${err.status} ${err.message}`);
      continue;
    }
  }

  throw new Error("All Groq models unavailable");
}
```

## 429 Rate Limit — Immediate Actions

```bash
set -euo pipefail
# Check exact limit info
curl -si https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  2>/dev/null | grep -i "x-ratelimit\|retry-after"

# Options:
# 1. Wait for retry-after seconds
# 2. Switch to a different model (each model has separate limits)
# 3. Reduce request volume (disable non-critical features)
# 4. If persistent, upgrade Groq plan at console.groq.com
```

## 401 Auth Failure — Key Rotation

```bash
set -euo pipefail
# 1. Verify current key
echo "Current key prefix: ${GROQ_API_KEY:0:8}"

# 2. Create new key at console.groq.com/keys
# 3. Test new key
curl -s -o /dev/null -w "%{http_code}" \
  https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $NEW_GROQ_KEY"

# 4. Deploy new key to production
# 5. Delete old key in console
```
