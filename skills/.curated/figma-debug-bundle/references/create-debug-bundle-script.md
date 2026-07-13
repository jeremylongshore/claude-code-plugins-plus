# Step 1: Create Debug Bundle Script

Deep-dive reference for the `figma-debug-bundle` skill — extracted from the 'Step 1: Create Debug Bundle Script' step of the workflow.

```bash
#!/bin/bash
# figma-debug-bundle.sh
set -euo pipefail

BUNDLE_DIR="figma-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Figma Debug Bundle ===" | tee "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$BUNDLE_DIR/summary.txt"
echo "---" >> "$BUNDLE_DIR/summary.txt"

# 1. Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "OS: $(uname -srm)" >> "$BUNDLE_DIR/summary.txt"
echo "PAT configured: ${FIGMA_PAT:+YES (${#FIGMA_PAT} chars)}" >> "$BUNDLE_DIR/summary.txt"
echo "File key: ${FIGMA_FILE_KEY:-NOT SET}" >> "$BUNDLE_DIR/summary.txt"

# 2. API connectivity test
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
echo -n "GET /v1/me: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o "$BUNDLE_DIR/me.json" -w "%{http_code} %{time_total}s" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# 3. File access test (if key is set)
if [ -n "${FIGMA_FILE_KEY:-}" ]; then
  echo -n "GET /v1/files: " >> "$BUNDLE_DIR/summary.txt"
  curl -s -o "$BUNDLE_DIR/file-meta.json" -w "%{http_code} %{time_total}s" \
    -H "X-Figma-Token: ${FIGMA_PAT}" \
    "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}?depth=1" >> "$BUNDLE_DIR/summary.txt"
  echo "" >> "$BUNDLE_DIR/summary.txt"
fi

# 4. Rate limit check (capture response headers)
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Rate Limit Headers ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -D "$BUNDLE_DIR/headers.txt" -o /dev/null \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me
grep -iE "(rate|retry|figma)" "$BUNDLE_DIR/headers.txt" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null || echo "No rate limit headers" >> "$BUNDLE_DIR/summary.txt"

# 5. Redact sensitive data
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Redaction ---" >> "$BUNDLE_DIR/summary.txt"
# Remove email from /v1/me response
if [ -f "$BUNDLE_DIR/me.json" ]; then
  jq '{handle: .handle, id: .id, img_url: "[REDACTED]", email: "[REDACTED]"}' \
    "$BUNDLE_DIR/me.json" > "$BUNDLE_DIR/me-redacted.json" 2>/dev/null || true
  rm -f "$BUNDLE_DIR/me.json"
fi

# Remove raw headers (may contain token in other tools)
rm -f "$BUNDLE_DIR/headers.txt"

echo "Redaction complete" >> "$BUNDLE_DIR/summary.txt"

# 6. Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
