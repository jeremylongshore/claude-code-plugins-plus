# Deepgram Debug Bundle - Implementation Details

## Environment Information Script
```bash
#!/bin/bash
# debug-env.sh

echo "=== Environment Info ===" > debug-bundle.txt
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> debug-bundle.txt
echo "OS: $(uname -a)" >> debug-bundle.txt
echo "Node: $(node --version 2>/dev/null || echo 'N/A')" >> debug-bundle.txt
echo "Python: $(python3 --version 2>/dev/null || echo 'N/A')" >> debug-bundle.txt
echo "" >> debug-bundle.txt

echo "=== SDK Versions ===" >> debug-bundle.txt
npm list @deepgram/sdk 2>/dev/null >> debug-bundle.txt
pip show deepgram-sdk 2>/dev/null >> debug-bundle.txt
```

## API Connectivity Test
```bash
#!/bin/bash
# debug-connectivity.sh

echo "=== API Connectivity ===" >> debug-bundle.txt

# Test REST API
echo "REST API:" >> debug-bundle.txt
curl -s -o /dev/null -w "%{http_code}" \
  -X GET 'https://api.deepgram.com/v1/projects' \
  -H "Authorization: Token $DEEPGRAM_API_KEY" >> debug-bundle.txt
echo "" >> debug-bundle.txt

# Test WebSocket
echo "WebSocket endpoint reachable:" >> debug-bundle.txt
curl -s -o /dev/null -w "%{http_code}" \
  -X GET 'https://api.deepgram.com/v1/listen' \
  -H "Authorization: Token $DEEPGRAM_API_KEY" >> debug-bundle.txt
```

## Request Logger
```typescript
// debug-logger.ts
import { createClient } from '@deepgram/sdk';
import { writeFileSync, appendFileSync } from 'fs';

interface DebugLog {
  timestamp: string;
  requestId?: string;
  operation: string;
  request: {
    url: string;
    options: Record<string, unknown>;
    audioSize?: number;
  };
  response?: {
    status: number;
    body: unknown;
    duration: number;
  };
  error?: {
    code: string;
    message: string;
    stack?: string;
  };
}

export class DeepgramDebugger {
  private logs: DebugLog[] = [];
  private client;

  constructor(apiKey: string) {
    this.client = createClient(apiKey);
  }

  async transcribeWithDebug(
    audioUrl: string,
    options: Record<string, unknown> = {}
  ) {
    const log: DebugLog = {
      timestamp: new Date().toISOString(),
      operation: 'transcribeUrl',
      request: { url: audioUrl, options },
    };

    const startTime = Date.now();

    try {
      const { result, error } = await this.client.listen.prerecorded.transcribeUrl(
        { url: audioUrl },
        { model: 'nova-2', ...options }
      );

      log.response = {
        status: error ? 400 : 200,
        body: result || error,
        duration: Date.now() - startTime,
      };

      if (result?.metadata?.request_id) {
        log.requestId = result.metadata.request_id;
      }

      if (error) {
        log.error = {
          code: error.code || 'UNKNOWN',
          message: error.message || 'Unknown error',
        };
      }
    } catch (err) {
      log.error = {
        code: 'EXCEPTION',
        message: err instanceof Error ? err.message : String(err),
        stack: err instanceof Error ? err.stack : undefined,
      };
      log.response = {
        status: 0,
        body: null,
        duration: Date.now() - startTime,
      };
    }

    this.logs.push(log);
    return log;
  }

  exportLogs(filePath: string = './deepgram-debug.json') {
    writeFileSync(filePath, JSON.stringify(this.logs, null, 2));
    console.log(`Debug logs exported to ${filePath}`);
  }

  exportForSupport() {
    const sanitized = this.logs.map(log => ({
      ...log,
      request: { ...log.request },
    }));

    return {
      timestamp: new Date().toISOString(),
      logs: sanitized,
      summary: {
        totalRequests: this.logs.length,
        failedRequests: this.logs.filter(l => l.error).length,
        averageDuration: this.logs.reduce((sum, l) =>
          sum + (l.response?.duration || 0), 0) / this.logs.length,
      },
    };
  }
}
```

## Minimal Reproduction Script
```typescript
// debug-repro.ts
import { createClient } from '@deepgram/sdk';

async function reproduce() {
  console.log('Starting reproduction...');
  console.log('SDK Version:', require('@deepgram/sdk/package.json').version);
  console.log('Node Version:', process.version);

  const client = createClient(process.env.DEEPGRAM_API_KEY!);

  try {
    const { result, error } = await client.listen.prerecorded.transcribeUrl(
      { url: 'https://static.deepgram.com/examples/nasa-podcast.wav' },
      { model: 'nova-2' }
    );

    if (error) {
      console.error('Error:', JSON.stringify(error, null, 2));
    } else {
      console.log('Success:', result.metadata.request_id);
    }
  } catch (err) {
    console.error('Exception:', err);
  }
}

reproduce();
```

## Audio Analysis Script
```bash
#!/bin/bash
# debug-audio.sh

AUDIO_FILE=$1

echo "=== Audio Analysis ===" >> debug-bundle.txt
echo "File: $AUDIO_FILE" >> debug-bundle.txt
echo "Size: $(stat -f%z "$AUDIO_FILE" 2>/dev/null || stat -c%s "$AUDIO_FILE")" >> debug-bundle.txt

if command -v ffprobe &> /dev/null; then
  echo "FFprobe output:" >> debug-bundle.txt
  ffprobe -v quiet -print_format json -show_format -show_streams "$AUDIO_FILE" >> debug-bundle.txt
fi
```

## Complete Debug Bundle Script
```bash
#!/bin/bash
# collect-debug-bundle.sh

BUNDLE_DIR="deepgram-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

echo "Collecting Deepgram debug bundle..."

# 1. Environment info
./debug-env.sh > "$BUNDLE_DIR/environment.txt"

# 2. Connectivity test
./debug-connectivity.sh > "$BUNDLE_DIR/connectivity.txt"

# 3. Recent logs (sanitized)
grep -i deepgram /var/log/app/*.log 2>/dev/null | tail -100 > "$BUNDLE_DIR/app-logs.txt"

# 4. Audio file info (if provided)
if [ -n "$1" ]; then
  ./debug-audio.sh "$1" > "$BUNDLE_DIR/audio-analysis.txt"
fi

# 5. Package info
cat > "$BUNDLE_DIR/README.txt" << EOF
Deepgram Debug Bundle
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)

Contents:
- environment.txt: System and SDK versions
- connectivity.txt: API connectivity tests
- app-logs.txt: Recent application logs
- audio-analysis.txt: Audio file details (if provided)

Issue Description:
[ADD YOUR ISSUE DESCRIPTION HERE]

Request IDs:
[ADD RELEVANT REQUEST IDS HERE]
EOF

tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Debug bundle created: $BUNDLE_DIR.tar.gz"
```

## Support Ticket Template
```markdown
## Issue Summary
[Brief description of the issue]

## Environment
- SDK: @deepgram/sdk v[VERSION]
- Node.js: v[VERSION]
- OS: [OS and version]

## Request ID(s)
- [request_id from response metadata]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Debug Bundle
[Attach debug-bundle.tar.gz]

## Audio Sample
[If applicable, attach sample audio or provide URL]
```
