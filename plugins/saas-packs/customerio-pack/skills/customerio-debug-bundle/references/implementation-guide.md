# Customerio Debug Bundle - Implementation Guide

# Customer.io Debug Bundle

## Overview
Collect comprehensive debug information for Customer.io support tickets and troubleshooting.

## Prerequisites
- Customer.io API credentials
- Access to application logs
- User ID or email of affected user

## Instructions

### Step 1: Create Debug Script
```bash
#!/bin/bash
# debug-customerio.sh

OUTPUT_DIR="customerio-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "Customer.io Debug Bundle" > "$OUTPUT_DIR/report.txt"
echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUTPUT_DIR/report.txt"
echo "" >> "$OUTPUT_DIR/report.txt"

# 1. API Connectivity Test
echo "=== API Connectivity ===" >> "$OUTPUT_DIR/report.txt"
curl -s -o "$OUTPUT_DIR/api-test.json" -w "%{http_code}" \
  -X GET "https://track.customer.io/api/v1/accounts" \
  -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_API_KEY" \
  >> "$OUTPUT_DIR/report.txt"
echo "" >> "$OUTPUT_DIR/report.txt"

# 2. SDK Version
echo "=== SDK Version ===" >> "$OUTPUT_DIR/report.txt"
npm list @customerio/track 2>/dev/null >> "$OUTPUT_DIR/report.txt" || echo "Not using npm" >> "$OUTPUT_DIR/report.txt"
pip show customerio 2>/dev/null >> "$OUTPUT_DIR/report.txt" || echo "Not using pip" >> "$OUTPUT_DIR/report.txt"
echo "" >> "$OUTPUT_DIR/report.txt"

# 3. Environment (redacted)
echo "=== Environment ===" >> "$OUTPUT_DIR/report.txt"
echo "CUSTOMERIO_SITE_ID: ${CUSTOMERIO_SITE_ID:0:8}..." >> "$OUTPUT_DIR/report.txt"
echo "CUSTOMERIO_API_KEY: ${CUSTOMERIO_API_KEY:0:8}..." >> "$OUTPUT_DIR/report.txt"
echo "NODE_ENV: $NODE_ENV" >> "$OUTPUT_DIR/report.txt"
echo "" >> "$OUTPUT_DIR/report.txt"

echo "Debug bundle created: $OUTPUT_DIR"
```

### Step 2: Collect User-Specific Data
```typescript
// scripts/debug-user.ts
import { TrackClient, RegionUS } from '@customerio/track';

async function debugUser(userId: string) {
  const debug: Record<string, any> = {
    timestamp: new Date().toISOString(),
    userId,
    checks: {}
  };

  const client = new TrackClient(
    process.env.CUSTOMERIO_SITE_ID!,
    process.env.CUSTOMERIO_API_KEY!,
    { region: RegionUS }
  );

  // Test identify call
  try {
    await client.identify(userId, { _debug_check: true });
    debug.checks.identify = { status: 'success' };
  } catch (error: any) {
    debug.checks.identify = {
      status: 'failed',
      error: error.message,
      code: error.statusCode
    };
  }

  // Test track call
  try {
    await client.track(userId, {
      name: '_debug_event',
      data: { timestamp: Date.now() }
    });
    debug.checks.track = { status: 'success' };
  } catch (error: any) {
    debug.checks.track = {
      status: 'failed',
      error: error.message,
      code: error.statusCode
    };
  }

  console.log(JSON.stringify(debug, null, 2));
  return debug;
}

// Run with: npx ts-node scripts/debug-user.ts user-123
debugUser(process.argv[2] || 'debug-user');
```

### Step 3: Collect Application Logs
```typescript
// lib/customerio-logger.ts
import { createWriteStream } from 'fs';

class CustomerIOLogger {
  private logStream: NodeJS.WritableStream;

  constructor(logPath: string = './customerio-debug.log') {
    this.logStream = createWriteStream(logPath, { flags: 'a' });
  }

  log(event: {
    type: 'identify' | 'track' | 'error';
    userId?: string;
    data?: any;
    error?: any;
    duration?: number;
  }) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      ...event
    };
    this.logStream.write(JSON.stringify(logEntry) + '\n');
  }

  // Wrap SDK calls with logging
  async wrapIdentify(
    client: TrackClient,
    userId: string,
    attributes: any
  ) {
    const start = Date.now();
    try {
      await client.identify(userId, attributes);
      this.log({
        type: 'identify',
        userId,
        data: attributes,
        duration: Date.now() - start
      });
    } catch (error: any) {
      this.log({
        type: 'error',
        userId,
        data: attributes,
        error: { message: error.message, code: error.statusCode },
        duration: Date.now() - start
      });
      throw error;
    }
  }
}
```

### Step 4: Generate Support Report
```typescript
// scripts/generate-support-report.ts
interface SupportReport {
  summary: string;
  environment: {
    sdkVersion: string;
    nodeVersion: string;
    region: string;
  };
  timeline: Array<{
    timestamp: string;
    event: string;
    details: string;
  }>;
  reproduction: {
    steps: string[];
    expected: string;
    actual: string;
  };
  evidence: {
    logs: string[];
    screenshots: string[];
    apiResponses: string[];
  };
}

function generateReport(): SupportReport {
  return {
    summary: 'Brief description of the issue',
    environment: {
      sdkVersion: require('@customerio/track/package.json').version,
      nodeVersion: process.version,
      region: process.env.CUSTOMERIO_REGION || 'us'
    },
    timeline: [
      { timestamp: '2024-01-15T10:00:00Z', event: 'First occurrence', details: '...' }
    ],
    reproduction: {
      steps: [
        '1. Call identify with user data',
        '2. Call track with event',
        '3. Check dashboard for user'
      ],
      expected: 'User appears in People section',
      actual: 'User not found, 401 error returned'
    },
    evidence: {
      logs: ['./customerio-debug.log'],
      screenshots: [],
      apiResponses: ['./debug-bundle/api-test.json']
    }
  };
}
```

### Step 5: Bundle and Submit
```bash
#!/bin/bash
# Create debug bundle archive
DEBUG_DIR="customerio-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$DEBUG_DIR"

# Collect all debug files
cp customerio-debug.log "$DEBUG_DIR/" 2>/dev/null
cp -r debug-bundle/* "$DEBUG_DIR/" 2>/dev/null

# Redact sensitive data
sed -i 's/api_key=.*/api_key=REDACTED/g' "$DEBUG_DIR"/*.log 2>/dev/null
sed -i 's/"api_key":"[^"]*"/"api_key":"REDACTED"/g' "$DEBUG_DIR"/*.json 2>/dev/null

# Create archive
tar -czf "$DEBUG_DIR.tar.gz" "$DEBUG_DIR"
echo "Debug bundle ready: $DEBUG_DIR.tar.gz"
echo "Submit to: support@customer.io"
```

## Output
- Debug script for API testing
- User-specific diagnostic data
- Application log collection
- Support report template
- Compressed debug bundle

## Error Handling
| Issue | Solution |
|-------|----------|
| Logs too large | Use `tail -n 1000` to limit |
| Sensitive data | Use redaction script |
| Missing permissions | Check file read access |

## Resources
- [Customer.io Support](https://customer.io/contact/)
- [API Status](https://status.customer.io/)

## Next Steps
After creating debug bundle, proceed to `customerio-rate-limits` to understand API limits.
