# Apollo Debug Bundle - Implementation Guide

> Full implementation details and code examples for the `apollo-debug-bundle` skill.

# Apollo Debug Bundle

## Overview
Collect comprehensive debug information for Apollo.io API issues to expedite support resolution.

## Debug Collection Script

```typescript
// scripts/apollo-debug-bundle.ts
import { writeFileSync } from 'fs';
import axios from 'axios';

interface DebugBundle {
  timestamp: string;
  environment: Record<string, any>;
  connectivity: Record<string, any>;
  apiHealth: Record<string, any>;
  recentRequests: Array<any>;
  errors: Array<any>;
}

async function collectDebugBundle(): Promise<DebugBundle> {
  const bundle: DebugBundle = {
    timestamp: new Date().toISOString(),
    environment: {},
    connectivity: {},
    apiHealth: {},
    recentRequests: [],
    errors: [],
  };

  // 1. Environment Info
  bundle.environment = {
    nodeVersion: process.version,
    platform: process.platform,
    arch: process.arch,
    apiKeyPresent: !!process.env.APOLLO_API_KEY,
    apiKeyLength: process.env.APOLLO_API_KEY?.length || 0,
    apiKeyPrefix: process.env.APOLLO_API_KEY?.substring(0, 8) + '...',
  };

  // 2. Connectivity Check
  try {
    const start = Date.now();
    await axios.get('https://api.apollo.io', { timeout: 5000 });
    bundle.connectivity = {
      reachable: true,
      latencyMs: Date.now() - start,
    };
  } catch (error: any) {
    bundle.connectivity = {
      reachable: false,
      error: error.message,
      code: error.code,
    };
  }

  // 3. API Health Check
  try {
    const response = await axios.get('https://api.apollo.io/v1/auth/health', {
      params: { api_key: process.env.APOLLO_API_KEY },
      timeout: 10000,
    });
    bundle.apiHealth = {
      status: 'healthy',
      responseCode: response.status,
      responseTime: response.headers['x-response-time'],
    };
  } catch (error: any) {
    bundle.apiHealth = {
      status: 'unhealthy',
      error: error.message,
      responseCode: error.response?.status,
      responseBody: sanitizeResponse(error.response?.data),
    };
  }

  // 4. Test Basic Endpoints
  const endpoints = [
    { name: 'people_search', method: 'POST', url: '/people/search', data: { per_page: 1 } },
    { name: 'org_enrich', method: 'GET', url: '/organizations/enrich', params: { domain: 'apollo.io' } },
  ];

  for (const endpoint of endpoints) {
    try {
      const start = Date.now();
      const response = await axios({
        method: endpoint.method,
        url: `https://api.apollo.io/v1${endpoint.url}`,
        params: { api_key: process.env.APOLLO_API_KEY, ...endpoint.params },
        data: endpoint.data,
        timeout: 15000,
      });

      bundle.recentRequests.push({
        endpoint: endpoint.name,
        status: 'success',
        responseCode: response.status,
        latencyMs: Date.now() - start,
        rateLimitRemaining: response.headers['x-ratelimit-remaining'],
      });
    } catch (error: any) {
      bundle.errors.push({
        endpoint: endpoint.name,
        status: 'failed',
        error: error.message,
        responseCode: error.response?.status,
        responseBody: sanitizeResponse(error.response?.data),
      });
    }
  }

  return bundle;
}

function sanitizeResponse(data: any): any {
  if (!data) return null;
  // Remove sensitive data
  const sanitized = JSON.parse(JSON.stringify(data));
  if (sanitized.people) {
    sanitized.people = `[${sanitized.people.length} contacts]`;
  }
  return sanitized;
}

// Main execution
async function main() {
  console.log('Collecting Apollo debug bundle...\n');

  const bundle = await collectDebugBundle();

  // Display summary
  console.log('=== Apollo Debug Bundle ===\n');
  console.log(`Timestamp: ${bundle.timestamp}`);
  console.log(`Node: ${bundle.environment.nodeVersion}`);
  console.log(`API Key Present: ${bundle.environment.apiKeyPresent}`);
  console.log(`API Reachable: ${bundle.connectivity.reachable}`);
  console.log(`API Health: ${bundle.apiHealth.status}`);
  console.log(`Successful Tests: ${bundle.recentRequests.length}`);
  console.log(`Failed Tests: ${bundle.errors.length}`);

  // Save to file
  const filename = `apollo-debug-${Date.now()}.json`;
  writeFileSync(filename, JSON.stringify(bundle, null, 2));
  console.log(`\nBundle saved to: ${filename}`);

  // Display errors if any
  if (bundle.errors.length > 0) {
    console.log('\n=== Errors ===');
    bundle.errors.forEach(err => {
      console.log(`\n${err.endpoint}:`);
      console.log(`  Status: ${err.responseCode}`);
      console.log(`  Error: ${err.error}`);
    });
  }
}

main().catch(console.error);
```

## Quick Debug Commands

```bash
# Check API key format
echo "API Key Length: $(echo -n $APOLLO_API_KEY | wc -c)"
echo "API Key Prefix: ${APOLLO_API_KEY:0:8}..."

# Test connectivity
curl -w "\nTime: %{time_total}s\nStatus: %{http_code}\n" \
  -s -o /dev/null \
  "https://api.apollo.io"

# Test authentication
curl -s "https://api.apollo.io/v1/auth/health?api_key=$APOLLO_API_KEY" | jq

# Test people search
curl -s -X POST "https://api.apollo.io/v1/people/search" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "'$APOLLO_API_KEY'", "per_page": 1}' | jq

# Check rate limit headers
curl -I -s -X POST "https://api.apollo.io/v1/people/search" \
  -H "Content-Type: application/json" \
  -d '{"api_key": "'$APOLLO_API_KEY'", "per_page": 1}' \
  | grep -i "ratelimit\|x-"
```

## Debug Checklist

### 1. Environment Verification
- [ ] APOLLO_API_KEY environment variable is set
- [ ] API key is correct length (typically 20+ characters)
- [ ] No extra whitespace in API key
- [ ] Using correct environment (production vs sandbox)

### 2. Network Verification
- [ ] Can reach api.apollo.io via HTTPS
- [ ] No proxy/firewall blocking requests
- [ ] DNS resolving correctly
- [ ] SSL/TLS working properly

### 3. Request Verification
- [ ] Content-Type header is `application/json`
- [ ] Request body is valid JSON
- [ ] Required fields are present
- [ ] Array fields are arrays (not strings)

### 4. Rate Limit Verification
- [ ] Not exceeding 100 requests/minute
- [ ] Implementing proper backoff
- [ ] Respecting Retry-After headers

## Support Ticket Template

```markdown
## Apollo API Issue Report

**Date/Time:** [timestamp]
**Affected Endpoint:** [endpoint URL]
**Error Code:** [HTTP status code]

### Environment
- Node.js Version: [version]
- SDK/Client: [axios version or other]
- Operating System: [OS]
- API Key Prefix: [first 8 chars]...

### Request Details
```json
{
  "method": "[GET/POST]",
  "url": "[full URL]",
  "headers": "[relevant headers]",
  "body": "[sanitized request body]"
}
```

### Response
```json
{
  "status": "[status code]",
  "body": "[error response]"
}
```

### Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happened]

### Debug Bundle
[Attach apollo-debug-*.json file]
```

## Output
- Comprehensive debug JSON bundle
- Environment verification results
- API connectivity status
- Recent request/response samples
- Ready-to-submit support ticket

## Error Handling
| Issue | Debug Step |
|-------|------------|
| Connection timeout | Check network/firewall |
| 401 errors | Verify API key |
| 429 errors | Check rate limit status |
| 500 errors | Check Apollo status page |

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support Portal](https://support.apollo.io)
- [Apollo API Documentation](https://apolloio.github.io/apollo-api-docs/)

## Next Steps
Proceed to `apollo-rate-limits` for rate limiting implementation.
