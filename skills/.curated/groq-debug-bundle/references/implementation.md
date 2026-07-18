# Groq Debug Bundle — Full Implementation

The complete six-step shell script that assembles a redacted Groq support bundle.
Run each step in order inside the same shell (they share `$BUNDLE_DIR`), or paste
the whole sequence into one script. Every write appends to a file inside
`$BUNDLE_DIR`, and Step 6 tars the directory and removes the working copy.

## Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
set -euo pipefail

BUNDLE_DIR="groq-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"
echo "Collecting Groq debug bundle..."

# === Environment ===
cat > "$BUNDLE_DIR/environment.txt" <<ENVEOF
=== Groq Debug Bundle ===
Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Hostname: $(hostname)
OS: $(uname -sr)
Node.js: $(node --version 2>/dev/null || echo 'not installed')
Python: $(python3 --version 2>/dev/null || echo 'not installed')
npm groq-sdk: $(npm list groq-sdk 2>/dev/null | grep groq-sdk || echo 'not installed')
pip groq: $(pip show groq 2>/dev/null | grep Version || echo 'not installed')
GROQ_API_KEY: ${GROQ_API_KEY:+SET (${#GROQ_API_KEY} chars, prefix: ${GROQ_API_KEY:0:4}...)}${GROQ_API_KEY:-NOT SET}
ENVEOF
```

## Step 2: API Connectivity Test

```bash
# Test API endpoint and capture headers
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/connectivity.txt"

# Models endpoint (lightweight, confirms auth)
curl -s -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
  https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  | jq '.data | length' >> "$BUNDLE_DIR/connectivity.txt" 2>&1

echo "Models available: $(curl -s https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY" | jq -r '.data[].id' | wc -l)" \
  >> "$BUNDLE_DIR/connectivity.txt"
```

## Step 3: Rate Limit Status

```bash
# Make a minimal request and capture rate limit headers
echo "--- Rate Limit Status ---" >> "$BUNDLE_DIR/rate-limits.txt"

curl -si https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"llama-3.1-8b-instant","messages":[{"role":"user","content":"ping"}],"max_tokens":1}' \
  2>/dev/null | grep -iE "^(x-ratelimit|retry-after|x-request-id)" \
  >> "$BUNDLE_DIR/rate-limits.txt"
```

## Step 4: Latency Benchmark

```bash
# Quick latency test across models
echo "--- Latency Benchmark ---" >> "$BUNDLE_DIR/latency.txt"

for model in "llama-3.1-8b-instant" "llama-3.3-70b-versatile"; do
  latency=$(curl -s -w "%{time_total}" -o /dev/null \
    https://api.groq.com/openai/v1/chat/completions \
    -H "Authorization: Bearer $GROQ_API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$model\",\"messages\":[{\"role\":\"user\",\"content\":\"ping\"}],\"max_tokens\":5}" \
    2>/dev/null)
  echo "$model: ${latency}s" >> "$BUNDLE_DIR/latency.txt"
done
```

## Step 5: Application Log Extraction

```bash
# Capture recent Groq-related errors from application logs (redacted)
echo "--- Application Logs (redacted) ---" >> "$BUNDLE_DIR/app-logs.txt"

# Node.js logs
if [ -d "logs" ]; then
  grep -i "groq\|rate.limit\|429\|api.error" logs/*.log 2>/dev/null | \
    tail -50 | \
    sed 's/gsk_[a-zA-Z0-9]*/gsk_***REDACTED***/g' \
    >> "$BUNDLE_DIR/app-logs.txt"
fi

# Config (redacted)
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/config-redacted.txt"
if [ -f ".env" ]; then
  sed 's/=.*/=***REDACTED***/' .env >> "$BUNDLE_DIR/config-redacted.txt"
fi
```

## Step 6: Package Bundle

```bash
# Create tarball
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Review before sharing -- ensure no secrets are included."
```

## ALWAYS Redact Before Sharing

- API keys (anything starting with `gsk_`)
- Bearer tokens
- PII (emails, names, IDs)
- Internal hostnames and IPs
