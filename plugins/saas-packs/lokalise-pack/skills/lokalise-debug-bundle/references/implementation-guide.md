# Lokalise Debug Bundle - Implementation Guide

Detailed implementation reference for the lokalise-debug-bundle skill.

## Instructions

### Step 1: Create Debug Bundle Script
```bash
#!/bin/bash
# lokalise-debug-bundle.sh

set -e

BUNDLE_DIR="lokalise-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "=== Lokalise Debug Bundle ===" > "$BUNDLE_DIR/summary.txt"
echo "Generated: $(date)" >> "$BUNDLE_DIR/summary.txt"
echo "Hostname: $(hostname)" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"
```

### Step 2: Collect Environment Info
```bash
# Environment info
echo "--- Environment ---" >> "$BUNDLE_DIR/summary.txt"
echo "Node version: $(node --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "npm version: $(npm --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "lokalise2 version: $(lokalise2 --version 2>/dev/null || echo 'not installed')" >> "$BUNDLE_DIR/summary.txt"
echo "LOKALISE_API_TOKEN: ${LOKALISE_API_TOKEN:+[SET - ${#LOKALISE_API_TOKEN} chars]}" >> "$BUNDLE_DIR/summary.txt"
echo "LOKALISE_PROJECT_ID: ${LOKALISE_PROJECT_ID:-[NOT SET]}" >> "$BUNDLE_DIR/summary.txt"
```

### Step 3: Gather SDK and Project Info
```bash
# SDK version
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- SDK Info ---" >> "$BUNDLE_DIR/summary.txt"
npm list @lokalise/node-api 2>/dev/null >> "$BUNDLE_DIR/summary.txt" || echo "SDK not installed" >> "$BUNDLE_DIR/summary.txt"

# Project info (if token is set)
if [ -n "$LOKALISE_API_TOKEN" ]; then
  echo "" >> "$BUNDLE_DIR/summary.txt"
  echo "--- Project Info ---" >> "$BUNDLE_DIR/summary.txt"

  # Get project details
  curl -s -X GET "https://api.lokalise.com/api2/projects" \
    -H "X-Api-Token: $LOKALISE_API_TOKEN" \
    | jq '.projects[] | {name, project_id, team_id, created_at}' \
    >> "$BUNDLE_DIR/projects.json" 2>/dev/null || echo "Failed to fetch projects" >> "$BUNDLE_DIR/summary.txt"
fi
```

### Step 4: Network and API Diagnostics
```bash
# Network connectivity test
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Network Tests ---" >> "$BUNDLE_DIR/summary.txt"

# DNS resolution
echo -n "DNS resolution: " >> "$BUNDLE_DIR/summary.txt"
host api.lokalise.com >> "$BUNDLE_DIR/summary.txt" 2>&1 || echo "FAILED" >> "$BUNDLE_DIR/summary.txt"

# API health check
echo -n "API Health: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{http_code}" "https://api.lokalise.com/api2/system/health" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Response time
echo -n "API Response Time: " >> "$BUNDLE_DIR/summary.txt"
curl -s -o /dev/null -w "%{time_total}s" "https://api.lokalise.com/api2/system/health" >> "$BUNDLE_DIR/summary.txt"
echo "" >> "$BUNDLE_DIR/summary.txt"

# Check rate limit headers
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Rate Limit Status ---" >> "$BUNDLE_DIR/summary.txt"
if [ -n "$LOKALISE_API_TOKEN" ]; then
  curl -s -I -X GET "https://api.lokalise.com/api2/projects" \
    -H "X-Api-Token: $LOKALISE_API_TOKEN" \
    | grep -i "x-ratelimit" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
fi
```

### Step 5: Collect Logs (Redacted)
```bash
# Recent application logs (redacted)
echo "" >> "$BUNDLE_DIR/summary.txt"
echo "--- Recent Logs (redacted) ---" >> "$BUNDLE_DIR/summary.txt"

# Search for Lokalise-related logs
if [ -d "./logs" ]; then
  grep -i "lokalise" ./logs/*.log 2>/dev/null | tail -100 \
    | sed 's/X-Api-Token: [^""]*/X-Api-Token: [REDACTED]/g' \
    | sed 's/apiKey": "[^"]*"/apiKey": "[REDACTED]"/g' \
    >> "$BUNDLE_DIR/logs-redacted.txt"
fi

# npm logs if available
if [ -d ~/.npm/_logs ]; then
  grep -l "lokalise" ~/.npm/_logs/*.log 2>/dev/null | tail -5 | while read f; do
    cat "$f" | sed 's/token=[^&]*/token=[REDACTED]/g' >> "$BUNDLE_DIR/npm-logs-redacted.txt"
  done
fi

# Config files (redacted)
echo "--- Config (redacted) ---" >> "$BUNDLE_DIR/summary.txt"
if [ -f ".env" ]; then
  grep -i lokalise .env 2>/dev/null | sed 's/=.*/=[REDACTED]/' >> "$BUNDLE_DIR/config-redacted.txt"
fi
if [ -f "lokalise.json" ]; then
  cat lokalise.json | jq 'del(.token)' >> "$BUNDLE_DIR/lokalise-config.json" 2>/dev/null
fi
```

### Step 6: Package Bundle
```bash
# Create archive
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"

echo ""
echo "Debug bundle created: $BUNDLE_DIR.tar.gz"
echo ""
echo "Contents:"
ls -la "$BUNDLE_DIR/"
echo ""
echo "IMPORTANT: Review the bundle for any remaining sensitive data before sharing!"

# Cleanup directory (keep tar.gz)
rm -rf "$BUNDLE_DIR"
```


## Detailed Examples

### Sensitive Data Handling
**ALWAYS REDACT:**
- API tokens
- Webhook secrets
- OAuth credentials
- Email addresses
- User IDs (if PII)

**Safe to Include:**
- Error messages
- Stack traces (redacted)
- SDK/runtime versions
- Project IDs (non-sensitive)
- HTTP status codes

### One-Liner Quick Check
```bash
# Quick API test
curl -s -w "\nStatus: %{http_code}\nTime: %{time_total}s\n" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" \
  "https://api.lokalise.com/api2/projects?limit=1" | jq '.projects[0].name // .error'
```

### Submit to Support
1. Run: `bash lokalise-debug-bundle.sh`
2. Review `*.tar.gz` contents for sensitive data
3. Email to [support@lokalise.com](mailto:support@lokalise.com) with:
   - Subject: "Support Request - [Brief Description]"
   - Body: Problem description, steps to reproduce
   - Attachment: Debug bundle

### TypeScript Debug Helper
```typescript
import { LokaliseApi } from "@lokalise/node-api";

async function collectDebugInfo() {
  const info: Record<string, any> = {
    timestamp: new Date().toISOString(),
    nodeVersion: process.version,
    platform: process.platform,
  };

  try {
    const client = new LokaliseApi({
      apiKey: process.env.LOKALISE_API_TOKEN!,
    });

    // Test API connection
    const start = Date.now();
    const projects = await client.projects().list({ limit: 1 });
    info.apiLatency = `${Date.now() - start}ms`;
    info.projectCount = projects.total_count;
  } catch (error: any) {
    info.error = {
      code: error.code,
      message: error.message,
    };
  }

  return info;
}
```

