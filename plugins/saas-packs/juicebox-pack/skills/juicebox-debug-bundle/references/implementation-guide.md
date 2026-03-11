# Juicebox Debug Bundle - Implementation Guide

Detailed implementation examples and code patterns.

## Instructions

### Step 1: Collect Environment Info
```bash
#!/bin/bash
# collect-debug-info.sh

echo "=== Juicebox Debug Bundle ===" > debug-bundle.txt
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> debug-bundle.txt
echo "" >> debug-bundle.txt

echo "=== Environment ===" >> debug-bundle.txt
echo "Node Version: $(node -v)" >> debug-bundle.txt
echo "NPM Version: $(npm -v)" >> debug-bundle.txt
echo "OS: $(uname -a)" >> debug-bundle.txt
echo "" >> debug-bundle.txt

echo "=== SDK Version ===" >> debug-bundle.txt
npm list @juicebox/sdk 2>/dev/null >> debug-bundle.txt
echo "" >> debug-bundle.txt
```

### Step 2: Test API Connectivity
```bash
echo "=== API Connectivity ===" >> debug-bundle.txt

# Health check
echo "Health Check:" >> debug-bundle.txt
curl -s -w "\nHTTP Status: %{http_code}\nTime: %{time_total}s\n" \
  https://api.juicebox.ai/v1/health >> debug-bundle.txt
echo "" >> debug-bundle.txt

# Auth verification (masked key)
echo "Auth Test:" >> debug-bundle.txt
MASKED_KEY="${JUICEBOX_API_KEY:0:10}...${JUICEBOX_API_KEY: -4}"
echo "API Key (masked): $MASKED_KEY" >> debug-bundle.txt
curl -s -w "\nHTTP Status: %{http_code}\n" \
  -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  https://api.juicebox.ai/v1/auth/me >> debug-bundle.txt
echo "" >> debug-bundle.txt
```

### Step 3: Gather Error Logs
```typescript
// debug/collect-logs.ts
import * as fs from 'fs';

export function collectRecentErrors(logPath: string): string[] {
  const logs = fs.readFileSync(logPath, 'utf-8');
  const lines = logs.split('\n');

  // Filter for Juicebox-related errors in last 24 hours
  const cutoff = Date.now() - 24 * 60 * 60 * 1000;

  return lines.filter(line => {
    if (!line.includes('juicebox') && !line.includes('Juicebox')) {
      return false;
    }
    const match = line.match(/\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/);
    if (match) {
      const timestamp = new Date(match[0]).getTime();
      return timestamp > cutoff;
    }
    return true;
  });
}
```

### Step 4: Create Support Bundle
```typescript
// debug/create-bundle.ts
import * as fs from 'fs';
import * as path from 'path';

interface DebugBundle {
  timestamp: string;
  environment: Record<string, string>;
  sdkVersion: string;
  recentErrors: string[];
  apiTests: {
    health: boolean;
    auth: boolean;
    latency: number;
  };
  requestSample?: {
    endpoint: string;
    request: any;
    response: any;
    duration: number;
  };
}

export async function createDebugBundle(): Promise<DebugBundle> {
  const bundle: DebugBundle = {
    timestamp: new Date().toISOString(),
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch
    },
    sdkVersion: require('@juicebox/sdk/package.json').version,
    recentErrors: collectRecentErrors('logs/app.log'),
    apiTests: await runApiTests()
  };

  // Save bundle
  const filename = `debug-bundle-${Date.now()}.json`;
  fs.writeFileSync(filename, JSON.stringify(bundle, null, 2));

  console.log(`Debug bundle saved to ${filename}`);
  return bundle;
}
```

## Checklist for Support Tickets

```markdown

## Support Ticket Template

**Issue Description:**
[Brief description of the problem]

**Steps to Reproduce:**
1.
2.
3.

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Debug Bundle Attached:**
- [ ] debug-bundle.json
- [ ] Relevant log excerpts
- [ ] Screenshot (if UI related)

**Environment:**
- SDK Version:
- Node Version:
- Platform:
```
