# Triage & Diagnostics

Deterministic checks to run first when a Groq incident is suspected. Each block is copy-paste ready and safe (read-only probes plus one 1-token ping per model).

## Severity Levels

| Level | Definition | Response Time | Examples |
|-------|------------|---------------|----------|
| P1 | Complete API failure | < 15 min | Groq API returns 5xx on all models |
| P2 | Degraded performance | < 1 hour | High latency, partial 429s, one model down |
| P3 | Minor impact | < 4 hours | Intermittent errors, non-critical feature affected |
| P4 | No user impact | Next business day | Monitoring gap, cost anomaly |

## Quick Triage (Run First)

```bash
set -euo pipefail
echo "=== 1. Groq API Status ==="
curl -sf https://status.groq.com > /dev/null && echo "status.groq.com: REACHABLE" || echo "status.groq.com: UNREACHABLE"

echo ""
echo "=== 2. API Authentication ==="
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY")
echo "GET /models: HTTP $HTTP_CODE"

echo ""
echo "=== 3. Model Availability ==="
for model in "llama-3.1-8b-instant" "llama-3.3-70b-versatile"; do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    https://api.groq.com/openai/v1/chat/completions \
    -H "Authorization: Bearer $GROQ_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":1}")
  echo "$model: HTTP $CODE"
done

echo ""
echo "=== 4. Rate Limit Status ==="
curl -si https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  2>/dev/null | grep -iE "^(x-ratelimit|retry-after)" || echo "No rate limit headers"
```

## Decision Tree

Map the triage output to an action path:

```
Is the Groq API responding?
├─ NO (timeout/connection refused):
│   ├─ Check status.groq.com
│   │   ├─ Incident reported → Wait, enable fallback provider
│   │   └─ No incident → Network issue on our side (check DNS, firewall, proxy)
│   └─ Check if api.groq.com resolves: dig api.groq.com
│
├─ YES, but 401/403:
│   ├─ API key revoked or expired → Rotate key
│   └─ Key not set in environment → Check secret manager
│
├─ YES, but 429:
│   ├─ retry-after header present → Wait that many seconds
│   ├─ All models 429 → Org-level limit hit; reduce traffic or upgrade plan
│   └─ One model 429 → Route to a different model
│
├─ YES, but 500/503:
│   ├─ One model → Groq capacity issue on that model; use fallback model
│   └─ All models → Groq-wide outage; enable fallback provider
│
└─ YES, but slow (latency > 2s):
    ├─ Large prompts → Reduce input size
    ├─ 70B model → Switch to 8B for speed
    └─ queue_time high → Groq queue congestion; try different model
```
