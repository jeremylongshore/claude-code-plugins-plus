# Lindy Debug Bundle - Implementation Guide

# Lindy Debug Bundle

## Overview
Comprehensive debugging toolkit for collecting diagnostics and resolving issues.

## Prerequisites
- Lindy SDK installed
- Access to logs
- curl installed for API testing

## Instructions

### Step 1: Collect Environment Info
```bash
#!/bin/bash
echo "=== Lindy Debug Bundle ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Node: $(node -v)"
echo "npm: $(npm -v)"
echo ""

echo "=== SDK Version ==="
npm list @lindy-ai/sdk 2>/dev/null || echo "SDK not found"
echo ""

echo "=== Environment ==="
echo "LINDY_API_KEY: ${LINDY_API_KEY:+[SET]}"
echo "LINDY_ENVIRONMENT: ${LINDY_ENVIRONMENT:-[NOT SET]}"
echo ""
```

### Step 2: Test API Connectivity
```bash
echo "=== API Connectivity ==="
curl -s -o /dev/null -w "Status: %{http_code}\nTime: %{time_total}s\n" \
  -H "Authorization: Bearer $LINDY_API_KEY" \
  https://api.lindy.ai/v1/users/me
echo ""
```

### Step 3: Collect Agent State
```typescript
// debug/collect-agent-state.ts
import { Lindy } from '@lindy-ai/sdk';

async function collectAgentState(agentId: string) {
  const lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });

  const bundle = {
    timestamp: new Date().toISOString(),
    agent: await lindy.agents.get(agentId),
    runs: await lindy.runs.list({ agentId, limit: 10 }),
    automations: await lindy.automations.list({ agentId }),
  };

  return bundle;
}

// Export for support
const state = await collectAgentState(process.argv[2]);
console.log(JSON.stringify(state, null, 2));
```

### Step 4: Check Run History
```typescript
async function analyzeRuns(agentId: string) {
  const lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });

  const runs = await lindy.runs.list({ agentId, limit: 50 });

  const analysis = {
    total: runs.length,
    successful: runs.filter(r => r.status === 'completed').length,
    failed: runs.filter(r => r.status === 'failed').length,
    avgDuration: runs.reduce((a, r) => a + r.duration, 0) / runs.length,
    recentErrors: runs
      .filter(r => r.status === 'failed')
      .slice(0, 5)
      .map(r => ({ id: r.id, error: r.error })),
  };

  return analysis;
}
```

### Step 5: Generate Support Bundle
```typescript
async function generateSupportBundle(agentId: string) {
  const bundle = {
    generated: new Date().toISOString(),
    environment: {
      node: process.version,
      platform: process.platform,
      sdk: require('@lindy-ai/sdk/package.json').version,
    },
    agent: await collectAgentState(agentId),
    analysis: await analyzeRuns(agentId),
  };

  const filename = `lindy-debug-${Date.now()}.json`;
  fs.writeFileSync(filename, JSON.stringify(bundle, null, 2));
  console.log(`Bundle saved to: ${filename}`);

  return filename;
}
```

## Output
- Environment diagnostic information
- API connectivity test results
- Agent state and configuration
- Run history analysis
- Exportable support bundle

## Error Handling
| Issue | Diagnostic | Resolution |
|-------|------------|------------|
| Auth fails | Check API key | Regenerate key |
| Timeout | Check network | Verify firewall |
| Agent missing | Check environment | Verify agent ID |

## Examples

### Quick Health Check
```bash
# One-liner health check
curl -s -H "Authorization: Bearer $LINDY_API_KEY" \
  https://api.lindy.ai/v1/users/me | jq '.email'
```

### Full Debug Script
```bash
#!/bin/bash
# save as lindy-debug.sh

echo "Collecting Lindy debug info..."
npx ts-node debug/collect-agent-state.ts $1 > debug-bundle.json
echo "Bundle saved to debug-bundle.json"
```

## Resources
- [Lindy Support](https://support.lindy.ai)
- [Status Page](https://status.lindy.ai)
- [API Reference](https://docs.lindy.ai/api)

## Next Steps
Proceed to `lindy-rate-limits` for rate limit management.
