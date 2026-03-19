---
name: twinmind-debug-bundle
description: |
  Collect comprehensive diagnostic information for TwinMind issues.
  Use when preparing support requests, investigating complex problems,
  or gathering evidence for bug reports.
  Trigger with phrases like "twinmind debug", "twinmind diagnostics",
  "collect twinmind info", "twinmind support bundle".
allowed-tools: Read, Write, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Overview
Collect comprehensive diagnostic data to troubleshoot TwinMind issues.

## Prerequisites
- TwinMind extension or API configured
- Access to browser developer tools
- Command-line access (for API debugging)

## Instructions

### Step 1: Create Debug Bundle Script

```typescript
// scripts/twinmind-debug-bundle.ts
import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

interface DebugBundle {
  timestamp: string;
  environment: EnvironmentInfo;
  apiStatus: ApiStatus;
  recentErrors: ErrorEntry[];
  configuration: ConfigSnapshot;
  networkTests: NetworkTest[];
}

interface EnvironmentInfo {
  nodeVersion: string;
  platform: string;
  arch: string;
  osRelease: string;
  timezone: string;
  memory: {
    total: number;
    free: number;
    used: number;
  };
}

interface ApiStatus {
  healthy: boolean;
  latencyMs: number;
  endpoint: string;
  responseHeaders?: Record<string, string>;
}

interface ErrorEntry {
  timestamp: string;
  type: string;
  message: string;
  stack?: string;
  context?: Record<string, any>;
}

interface ConfigSnapshot {
  apiKeyPresent: boolean;
  apiKeyPrefix: string;
  baseUrl: string;
  timeout: number;
  environment: string;
}

interface NetworkTest {
  endpoint: string;
  reachable: boolean;
  latencyMs?: number;
  error?: string;
}

export async function generateDebugBundle(): Promise<DebugBundle> {
  const bundle: DebugBundle = {
    timestamp: new Date().toISOString(),
    environment: getEnvironmentInfo(),
    apiStatus: await checkApiStatus(),
    recentErrors: collectRecentErrors(),
    configuration: getConfigSnapshot(),
    networkTests: await runNetworkTests(),
  };

  return bundle;
}

function getEnvironmentInfo(): EnvironmentInfo {
  return {
    nodeVersion: process.version,
    platform: os.platform(),
    arch: os.arch(),
    osRelease: os.release(),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    memory: {
      total: os.totalmem(),
      free: os.freemem(),
      used: os.totalmem() - os.freemem(),
    },
  };
}

async function checkApiStatus(): Promise<ApiStatus> {
  const endpoint = process.env.TWINMIND_API_URL || 'https://api.twinmind.com/v1';
  const start = Date.now();

  try {
    const response = await fetch(`${endpoint}/health`, {
      headers: {
        'Authorization': `Bearer ${process.env.TWINMIND_API_KEY}`,
      },
    });

    return {
      healthy: response.ok,
      latencyMs: Date.now() - start,
      endpoint,
      responseHeaders: Object.fromEntries(response.headers.entries()),
    };
  } catch (error: any) {
    return {
      healthy: false,
      latencyMs: Date.now() - start,
      endpoint,
    };
  }
}

function collectRecentErrors(): ErrorEntry[] {
  // In a real implementation, this would read from error logs
  // For now, return empty array
  return [];
}

function getConfigSnapshot(): ConfigSnapshot {
  const apiKey = process.env.TWINMIND_API_KEY || '';

  return {
    apiKeyPresent: apiKey.length > 0,
    apiKeyPrefix: apiKey.substring(0, 8) + '...',
    baseUrl: process.env.TWINMIND_API_URL || 'https://api.twinmind.com/v1',
    timeout: parseInt(process.env.TWINMIND_TIMEOUT || '30000'),  # 30000: 30 seconds in ms
    environment: process.env.NODE_ENV || 'development',
  };
}

async function runNetworkTests(): Promise<NetworkTest[]> {
  const endpoints = [
    'https://api.twinmind.com',
    'https://status.twinmind.com',
    'https://twinmind.com',
  ];

  const tests: NetworkTest[] = [];

  for (const endpoint of endpoints) {
    const start = Date.now();
    try {
      const response = await fetch(endpoint, { method: 'HEAD' });
      tests.push({
        endpoint,
        reachable: response.ok,
        latencyMs: Date.now() - start,
      });
    } catch (error: any) {
      tests.push({
        endpoint,
        reachable: false,
        error: error.message,
      });
    }
  }

  return tests;
}

// Save bundle to file
export async function saveDebugBundle(outputPath?: string): Promise<string> {
  const bundle = await generateDebugBundle();

  const filename = outputPath || path.join(
    os.tmpdir(),
    `twinmind-debug-${Date.now()}.json`
  );

  fs.writeFileSync(filename, JSON.stringify(bundle, null, 2));

  console.log(`Debug bundle saved to: ${filename}`);
  return filename;
}
```

### Step 2: Run Debug Bundle Collection

```bash
set -euo pipefail
# Using the script
npx ts-node scripts/twinmind-debug-bundle.ts

# Or quick CLI commands:

# Check API health
curl -w "\nLatency: %{time_total}s\n" \
  -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health

# Check account status
curl -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/me | jq

# Check rate limit status
curl -I -H "Authorization: Bearer $TWINMIND_API_KEY" \
  https://api.twinmind.com/v1/health 2>/dev/null | grep -i ratelimit

# Test transcription endpoint
curl -X POST \
  -H "Authorization: Bearer $TWINMIND_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"audio_url":"https://example.com/test.mp3"}' \
  https://api.twinmind.com/v1/transcribe
```

### Step 3: Browser Extension Debugging

```javascript
// Open Chrome DevTools (F12) on any TwinMind page
// Console commands for debugging:

// Check extension version
chrome.runtime.getManifest().version

// Check stored data
chrome.storage.local.get(null, console.log)

// Check permissions
navigator.permissions.query({name: 'microphone'}).then(console.log)

// Check audio devices
navigator.mediaDevices.enumerateDevices().then(devices => {
  console.log('Audio devices:', devices.filter(d => d.kind === 'audioinput'))
})

// Check extension errors
// Go to: chrome://extensions > TwinMind > Errors
```

### Step 4: Collect Network HAR File

```
1. Open Chrome DevTools (F12)
2. Go to Network tab
3. Check "Preserve log"
4. Reproduce the issue
5. Right-click > Save all as HAR with content
```

### Step 5: Generate Full Debug Report

```typescript
// scripts/full-debug-report.ts
import { generateDebugBundle } from './twinmind-debug-bundle';

async function generateFullReport() {
  const bundle = await generateDebugBundle();

  const report = `
# TwinMind Debug Report
Generated: ${bundle.timestamp}

## Environment
- Node: ${bundle.environment.nodeVersion}
- Platform: ${bundle.environment.platform} (${bundle.environment.arch})
- OS: ${bundle.environment.osRelease}
- Timezone: ${bundle.environment.timezone}
- Memory: ${Math.round(bundle.environment.memory.used / 1024 / 1024)}MB / ${Math.round(bundle.environment.memory.total / 1024 / 1024)}MB  # 1024: 1 KB

## API Status
- Healthy: ${bundle.apiStatus.healthy ? 'Yes' : 'No'}
- Latency: ${bundle.apiStatus.latencyMs}ms
- Endpoint: ${bundle.apiStatus.endpoint}

## Configuration
- API Key Present: ${bundle.configuration.apiKeyPresent}
- API Key Prefix: ${bundle.configuration.apiKeyPrefix}
- Base URL: ${bundle.configuration.baseUrl}
- Timeout: ${bundle.configuration.timeout}ms
- Environment: ${bundle.configuration.environment}

## Network Tests
${bundle.networkTests.map(t =>
  `- ${t.endpoint}: ${t.reachable ? `OK (${t.latencyMs}ms)` : `FAILED - ${t.error}`}`
).join('\n')}

## Recent Errors
${bundle.recentErrors.length === 0 ? 'No recent errors' :
  bundle.recentErrors.map(e =>
    `- [${e.timestamp}] ${e.type}: ${e.message}`
  ).join('\n')
}

## Troubleshooting Steps Taken
[ ] Verified API key is valid
[ ] Checked microphone permissions
[ ] Tested network connectivity
[ ] Cleared browser cache/data
[ ] Disabled conflicting extensions
[ ] Reproduced in incognito mode

## Issue Description
[Describe the issue here]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]
`;

  console.log(report);
  return report;
}

generateFullReport();
```

## Output
- JSON debug bundle file
- Environment information
- API connectivity status
- Network test results
- Configuration snapshot (no secrets)
- Debug report template

Example output:
```json
{
  "timestamp": "2025-01-15T10:30:00Z",  # 2025 year
  "environment": {
    "nodeVersion": "v20.10.0",
    "platform": "darwin",
    "arch": "arm64"
  },
  "apiStatus": {
    "healthy": true,
    "latencyMs": 145
  },
  "networkTests": [
    {"endpoint": "https://api.twinmind.com", "reachable": true, "latencyMs": 120}
  ]
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| API unreachable | Network/firewall | Check VPN/proxy settings |
| Auth failed | Invalid key | Regenerate API key |
| Timeout | Slow network | Increase timeout value |
| Missing env vars | Not configured | Check .env file |

## Information to Include in Support Request

1. **Debug bundle JSON** - Generated by this script
2. **HAR file** - Network requests during failure
3. **Console logs** - Browser or terminal errors
4. **Request ID** - From response headers (X-Request-Id)
5. **Timestamps** - When the issue occurred
6. **Steps to reproduce** - Detailed sequence

## Security Notes

The debug bundle intentionally excludes:
- Full API keys (only prefix shown)
- Audio content
- Transcript content
- Personal information
- OAuth tokens

Always review the bundle before sharing with support.

## Resources
- [TwinMind Support](https://twinmind.com/support)
- [TwinMind Status](https://status.twinmind.com)
- [Community Forum](https://community.twinmind.com)

## Next Steps
For rate limiting strategies, see `twinmind-rate-limits`.

## Examples

**Basic usage**: Apply twinmind debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind debug bundle for production environments with multiple constraints and team-specific requirements.