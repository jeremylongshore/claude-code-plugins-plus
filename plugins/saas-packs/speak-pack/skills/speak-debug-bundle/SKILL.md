---
name: speak-debug-bundle
description: |
  Collect Speak debug evidence for support tickets and troubleshooting.
  Use when encountering persistent issues, preparing support tickets,
  or collecting diagnostic information for Speak problems.
  Trigger with phrases like "speak debug", "speak support bundle",
  "collect speak logs", "speak diagnostic".
allowed-tools: Read, Bash(grep:*), Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect all necessary diagnostic information for Speak support tickets.

## Prerequisites
- Speak SDK installed
- Access to application logs
- Permission to collect environment info

## Instructions
1. **Complete Script**
2. **Sensitive Data Handling**
3. **Submit to Support**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- `speak-debug-YYYYMMDD-HHMMSS.tar.gz` archive containing:
  - `summary.txt` - Environment and SDK info
  - `logs.txt` - Recent redacted logs
  - `sessions.txt` - Recent session activity
  - `config-redacted.txt` - Configuration (secrets removed)

## Resources
- [Speak Support Portal](https://support.speak.com)
- [Speak Status](https://status.speak.com)
- [Developer Community](https://community.speak.com)

## Next Steps
For rate limit issues, see `speak-rate-limits`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with debugging |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

### Basic: Collect Debug Bundle
```bash
#!/bin/bash
BUNDLE_DIR="speak-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

# Environment info
node --version > "$BUNDLE_DIR/summary.txt" 2>&1
echo "OS: $(uname -a)" >> "$BUNDLE_DIR/summary.txt"
npm list --depth=0 2>/dev/null | grep -i speak >> "$BUNDLE_DIR/summary.txt"

# Redact API keys from config
cat .env 2>/dev/null | sed 's/=.*/=REDACTED/' > "$BUNDLE_DIR/config-redacted.txt"

# Recent logs (last 200 lines, secrets stripped)
tail -200 logs/speak.log 2>/dev/null | \
  sed -E 's/(Bearer |api_key=)[^ "]+/\1REDACTED/g' > "$BUNDLE_DIR/logs.txt"

# Package into archive
tar czf "${BUNDLE_DIR}.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: ${BUNDLE_DIR}.tar.gz"
```

### Advanced: Automated Debug Bundle with API Health Check
```typescript
import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";

interface HealthCheck {
  endpoint: string;
  status: number;
  latencyMs: number;
  error?: string;
}

async function collectSpeakDebugBundle(apiKey: string): Promise<string> {
  const bundleDir = `speak-debug-${Date.now()}`;
  fs.mkdirSync(bundleDir, { recursive: true });

  // Health check critical endpoints
  const endpoints = ["/v1/languages", "/v1/pronunciation/status", "/v1/conversation/status"];
  const checks: HealthCheck[] = [];
  for (const ep of endpoints) {
    const start = Date.now();
    try {
      const res = await fetch(`https://api.speak.com${ep}`, {
        headers: { Authorization: `Bearer ${apiKey}` },
      });
      checks.push({ endpoint: ep, status: res.status, latencyMs: Date.now() - start });
    } catch (err: any) {
      checks.push({ endpoint: ep, status: 0, latencyMs: Date.now() - start, error: err.message });
    }
  }
  fs.writeFileSync(path.join(bundleDir, "health-checks.json"), JSON.stringify(checks, null, 2));

  // Collect dependency versions
  const deps = execSync("npm list --depth=0 --json 2>/dev/null || echo '{}'").toString();
  fs.writeFileSync(path.join(bundleDir, "dependencies.json"), deps);

  // Create archive
  execSync(`tar czf "${bundleDir}.tar.gz" "${bundleDir}"`);
  return `${bundleDir}.tar.gz`;
}
```