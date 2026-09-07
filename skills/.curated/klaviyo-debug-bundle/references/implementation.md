# Klaviyo Debug Bundle — Full Shell Implementation

The complete `klaviyo-debug-bundle.sh` script, broken into the five build steps.
Assemble these blocks in order into a single file, `chmod +x`, and run from your
application root so the log-collection step can find `logs/`.

## Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# klaviyo-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="klaviyo-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Klaviyo Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

## Step 2: Collect Environment Info

```bash
# --- Runtime ---
echo "--- Runtime Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node.js: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -srm)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- SDK Version ---
echo "--- Klaviyo SDK ---" >> "$BUNDLE_DIR/summary.txt"
npm list klaviyo-api 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "klaviyo-api: not installed" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# --- API Key Check (redacted) ---
echo "--- API Key Status ---" >> "$BUNDLE_DIR/summary.txt"
if [ -n "${KLAVIYO_PRIVATE_KEY:-}" ]; then
  echo "KLAVIYO_PRIVATE_KEY: SET (${#KLAVIYO_PRIVATE_KEY} chars, prefix: ${KLAVIYO_PRIVATE_KEY:0:3}***)" >> "$BUNDLE_DIR/summary.txt"
else
  echo "KLAVIYO_PRIVATE_KEY: NOT SET" >> "$BUNDLE_DIR/summary.txt"
fi
echo "" >> "$BUNDLE_DIR/summary.txt"
```

## Step 3: API Connectivity Tests

The `revision` header pins the Klaviyo API version. `2024-10-15` is a stable
published revision date (Klaviyo versions its API by date, not a semver number),
so requests behave identically regardless of when the bundle is run.

```bash
# --- API Connectivity ---
echo "--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"

# Test base connectivity
echo -n "DNS resolve a.klaviyo.com: " >> "$BUNDLE_DIR/summary.txt"
nslookup a.klaviyo.com > /dev/null 2>&1 && echo "OK" >> "$BUNDLE_DIR/summary.txt" || echo "FAILED" >> "$BUNDLE_DIR/summary.txt"

# Test API authentication
if [ -n "${KLAVIYO_PRIVATE_KEY:-}" ]; then
  HTTP_CODE=$(curl -s -o "$BUNDLE_DIR/api-response.json" -w "%{http_code}" \
    -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
    -H "revision: 2024-10-15" \
    -H "Accept: application/vnd.api+json" \
    "https://a.klaviyo.com/api/accounts/" 2>/dev/null || echo "000")
  echo "API Auth Test: HTTP $HTTP_CODE" >> "$BUNDLE_DIR/summary.txt"

  # Capture rate limit headers
  curl -s -I \
    -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
    -H "revision: 2024-10-15" \
    "https://a.klaviyo.com/api/profiles/?page[size]=1" 2>/dev/null \
    | grep -i "ratelimit\|retry-after" >> "$BUNDLE_DIR/rate-limits.txt" || echo "No rate limit headers" >> "$BUNDLE_DIR/rate-limits.txt"
fi

# Check Klaviyo status page
echo -n "Status Page: " >> "$BUNDLE_DIR/summary.txt"
curl -s "https://status.klaviyo.com/api/v2/status.json" 2>/dev/null \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',{}).get('description','unknown'))" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null \
  || echo "Could not reach status page" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

## Step 4: Application Log Collection

```bash
# --- Recent Error Logs (redacted) ---
echo "--- Recent Klaviyo Errors ---" >> "$BUNDLE_DIR/summary.txt"

# Search common log locations for Klaviyo errors
for logdir in logs/ /var/log/app/; do
  if [ -d "$logdir" ]; then
    grep -i "klaviyo\|a\.klaviyo\.com" "$logdir"*.log 2>/dev/null \
      | tail -50 \
      | sed -E 's/pk_[a-zA-Z0-9]+/pk_***REDACTED***/g' \
      | sed -E 's/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/***@redacted***/g' \
      >> "$BUNDLE_DIR/recent-errors.txt"
  fi
done

# Redact any remaining secrets from all collected files
for file in "$BUNDLE_DIR"/*.txt "$BUNDLE_DIR"/*.json; do
  [ -f "$file" ] && sed -i -E 's/pk_[a-zA-Z0-9]{20,}/pk_***REDACTED***/g' "$file"
done
```

## Step 5: Package and Output

```bash
# Package bundle
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo ""
echo "Bundle created: $BUNDLE_DIR.tar.gz"
echo "Review before sharing -- ensure no secrets remain."
```
