## Implementation Guide

### Step 1: Create Debug Bundle Script

```bash
#!/bin/bash
# vercel-debug-bundle.sh

BUNDLE_DIR="vercel-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Vercel Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info

```bash
# Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
node --version >> "$BUNDLE_DIR/summary.txt" 2>&1
npm --version >> "$BUNDLE_DIR/summary.txt" 2>&1
echo "VERCEL_API_KEY: ${VERCEL_API_KEY:+[SET]}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Gather SDK and Logs

```bash
# SDK version
npm list vercel 2>/dev/null >> "$BUNDLE_DIR/summary.txt"

# Recent logs (redacted)
grep -i "vercel" ~/.npm/_logs/*.log 2>/dev/null | tail -50 >> "$BUNDLE_DIR/logs.txt"

# Configuration (redacted - secrets masked)
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
cat .env 2>/dev/null | sed 's/=.*/=***REDACTED***/' >> "$BUNDLE_DIR/config-redacted.txt"

# Network connectivity test
echo "--- Network Test ---" >> "$BUNDLE_DIR/summary.txt"
echo -n "API Health: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" https://api.vercel.com/health >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 4: Package Bundle

```bash
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
