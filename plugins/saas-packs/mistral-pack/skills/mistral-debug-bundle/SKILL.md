---
name: mistral-debug-bundle
description: |
  Collect Mistral AI debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Mistral AI problems.
  Trigger with phrases like "mistral debug", "mistral support bundle",
  "collect mistral logs", "mistral diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, debugging]

---
# Mistral AI Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`

## Overview
Collect all necessary diagnostic information for Mistral AI support tickets. Creates a redacted bundle with environment info, SDK versions, API connectivity test, available models, and recent error logs.

## Prerequisites
- Mistral AI SDK installed
- Access to application logs
- `MISTRAL_API_KEY` set (for connectivity test)

## Instructions

### Step 1: Complete Debug Script

```bash
#!/bin/bash
# mistral-debug-bundle.sh — Creates redacted support bundle
set -e

BUNDLE_DIR="mistral-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "Creating Mistral AI debug bundle..."

# === Environment Info ===
cat > "$BUNDLE_DIR/summary.txt" << EOF
=== Mistral AI Debug Bundle ===
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Hostname: $(hostname)

--- Environment ---
Node.js: $(node --version 2>/dev/null || echo 'not installed')
Python: $(python3 --version 2>/dev/null || echo 'not installed')
npm: $(npm --version 2>/dev/null || echo 'not installed')
OS: $(uname -a)
MISTRAL_API_KEY: ${MISTRAL_API_KEY:+[SET, length=${#MISTRAL_API_KEY}]}${MISTRAL_API_KEY:-[NOT SET]}
EOF

# === SDK Versions ===
echo -e "\n--- SDK Versions ---" >> "$BUNDLE_DIR/summary.txt"
npm list @mistralai/mistralai 2>/dev/null >> "$BUNDLE_DIR/summary.txt" \
  || echo "Node SDK: not installed" >> "$BUNDLE_DIR/summary.txt"
pip show mistralai 2>/dev/null | grep -E "^(Name|Version)" >> "$BUNDLE_DIR/summary.txt" \
  || echo "Python SDK: not installed" >> "$BUNDLE_DIR/summary.txt"

# === API Connectivity ===
echo -e "\n--- API Connectivity ---" >> "$BUNDLE_DIR/summary.txt"
if [ -n "${MISTRAL_API_KEY:-}" ]; then
  HTTP_STATUS=$(curl -s -o "$BUNDLE_DIR/api-response.json" -w "%{http_code}" \
    -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
    https://api.mistral.ai/v1/models 2>/dev/null)
  echo "HTTP Status: $HTTP_STATUS" >> "$BUNDLE_DIR/summary.txt"

  if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "\n--- Available Models ---" >> "$BUNDLE_DIR/summary.txt"
    jq -r '.data[].id' "$BUNDLE_DIR/api-response.json" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null
  fi
  rm -f "$BUNDLE_DIR/api-response.json"
else
  echo "Skipped (no API key)" >> "$BUNDLE_DIR/summary.txt"
fi

# === Dependencies ===
if [ -f "package.json" ]; then
  echo -e "\n--- Dependencies ---" >> "$BUNDLE_DIR/summary.txt"
  jq '{dependencies, devDependencies}' package.json 2>/dev/null >> "$BUNDLE_DIR/summary.txt"
fi

# === Recent Logs (redacted) ===
echo "--- Recent Logs (redacted) ---" > "$BUNDLE_DIR/logs.txt"
if [ -d "logs" ]; then
  grep -i "mistral\|error\|429\|401\|500" logs/*.log 2>/dev/null | tail -100 >> "$BUNDLE_DIR/logs.txt"
fi

# === Config (redacted) ===
if [ -f ".env" ]; then
  sed 's/=.*/=***REDACTED***/' .env > "$BUNDLE_DIR/config-redacted.txt"
fi

# === Reproduction Script ===
cat > "$BUNDLE_DIR/reproduce.sh" << 'SCRIPT'
#!/bin/bash
set -euo pipefail
curl -X POST https://api.mistral.ai/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${MISTRAL_API_KEY}" \
  -d '{"model":"mistral-small-latest","messages":[{"role":"user","content":"ping"}]}' 2>&1
echo -e "\nExit code: $?"
SCRIPT
chmod +x "$BUNDLE_DIR/reproduce.sh"

# === Package ===
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle: $BUNDLE_DIR.tar.gz"
echo "IMPORTANT: Review for sensitive data before sharing!"
```

### Step 2: TypeScript Debug Helper

```typescript
import { Mistral } from '@mistralai/mistralai';

interface DebugInfo {
  timestamp: string;
  nodeVersion: string;
  apiKeySet: boolean;
  apiKeyLength: number;
  connectivity: 'ok' | 'auth_error' | 'network_error' | 'unknown_error';
  availableModels: string[];
  latencyMs: number;
  lastError?: { message: string; status?: number };
}

async function collectDebugInfo(error?: Error): Promise<DebugInfo> {
  const info: DebugInfo = {
    timestamp: new Date().toISOString(),
    nodeVersion: process.version,
    apiKeySet: !!process.env.MISTRAL_API_KEY,
    apiKeyLength: process.env.MISTRAL_API_KEY?.length ?? 0,
    connectivity: 'unknown_error',
    availableModels: [],
    latencyMs: 0,
  };

  if (error) {
    info.lastError = {
      message: error.message,
      status: (error as any).status,
    };
  }

  if (info.apiKeySet) {
    const start = performance.now();
    try {
      const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });
      const models = await client.models.list();
      info.connectivity = 'ok';
      info.availableModels = models.data?.map(m => m.id) ?? [];
      info.latencyMs = Math.round(performance.now() - start);
    } catch (e: any) {
      info.latencyMs = Math.round(performance.now() - start);
      info.connectivity = e.status === 401 ? 'auth_error' : 'network_error';
    }
  }

  return info;
}

// Usage in catch blocks
try {
  await client.chat.complete({ model: 'mistral-small-latest', messages });
} catch (error) {
  const debug = await collectDebugInfo(error as Error);
  console.error('Debug info:', JSON.stringify(debug, null, 2));
}
```

### Step 3: Request/Response Logger for Debugging

```typescript
function createDebugClient(): Mistral {
  const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

  // Wrap chat.complete to log request/response metadata
  const originalComplete = client.chat.complete.bind(client.chat);
  client.chat.complete = async (params: any) => {
    const start = performance.now();
    console.debug('[MISTRAL REQUEST]', {
      model: params.model,
      messageCount: params.messages?.length,
      hasTools: !!params.tools?.length,
      temperature: params.temperature,
    });

    try {
      const response = await originalComplete(params);
      console.debug('[MISTRAL RESPONSE]', {
        durationMs: Math.round(performance.now() - start),
        finishReason: response.choices?.[0]?.finishReason,
        usage: response.usage,
        hasToolCalls: !!response.choices?.[0]?.message?.toolCalls?.length,
      });
      return response;
    } catch (error: any) {
      console.debug('[MISTRAL ERROR]', {
        durationMs: Math.round(performance.now() - start),
        status: error.status,
        message: error.message,
      });
      throw error;
    }
  };

  return client;
}
```

## Sensitive Data Rules

**ALWAYS REDACT:** API keys, passwords, PII (emails, names), internal URLs
**SAFE TO INCLUDE:** Error messages, stack traces, SDK versions, HTTP status codes, model IDs

## Output
- `mistral-debug-YYYYMMDD-HHMMSS.tar.gz` containing:
  - `summary.txt` — environment, SDK versions, API status
  - `logs.txt` — recent redacted error logs
  - `config-redacted.txt` — config with secrets masked
  - `reproduce.sh` — minimal reproduction script

## Error Handling
| Item | Purpose |
|------|---------|
| Environment versions | Compatibility check |
| SDK version | Version-specific bug identification |
| API connectivity test | Network/auth diagnosis |
| Available models | Key scope verification |
| Error logs (redacted) | Root cause analysis |

## Resources
- [Mistral AI Status](https://status.mistral.ai/)
- [Mistral AI Discord](https://discord.gg/mistralai)
- [API Reference](https://docs.mistral.ai/api/)

## Next Steps
For rate limit issues, see `mistral-rate-limits`. For common errors, see `mistral-common-errors`.
