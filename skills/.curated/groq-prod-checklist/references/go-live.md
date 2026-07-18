# Groq Go-Live Verification

The final pre-flight gate. Run this script against production immediately
before flipping traffic. Every line must pass before you go live.

## Verification Script

Requires `GROQ_API_KEY_PROD` exported in the environment and `jq` installed.
Confirms Groq's status page is green, the production key is valid, your health
endpoint is up, and there is real rate-limit headroom.

```bash
set -euo pipefail
# Pre-flight checks
echo "1. Groq API status..."
curl -sf https://status.groq.com > /dev/null && echo "OK" || echo "ISSUE"

echo "2. Production key valid..."
curl -sf https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY_PROD" | jq '.data | length'

echo "3. Health endpoint..."
curl -sf https://your-app.com/api/health | jq .

echo "4. Rate limit headroom..."
curl -si https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY_PROD" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  2>/dev/null | grep -i "x-ratelimit-remaining"
```

## Interpreting Results

| Check | Pass condition | If it fails |
|-------|----------------|-------------|
| 1. API status | Prints `OK` | Do not deploy — wait for status.groq.com to clear |
| 2. Key valid | Prints a model count > 0 | Key revoked or wrong env — regenerate in console |
| 3. Health endpoint | Returns `status: healthy` | App cannot reach Groq — check secrets injection |
| 4. Rate limit | Header present, remaining > 0 | Near a limit — request an increase before launch |
