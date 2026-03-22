---
name: deepgram-debug-bundle
description: |
  Collect Deepgram debug evidence for support and troubleshooting.
  Use when preparing support tickets, investigating issues,
  or collecting diagnostic information for Deepgram problems.
  Trigger: "deepgram debug", "deepgram support ticket", "collect deepgram logs",
  "deepgram diagnostic", "deepgram debug bundle".
allowed-tools: Read, Grep, Bash(curl:*), Bash(ffprobe:*), Bash(npm:*), Bash(tar:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, deepgram, debugging, support]

---
# Deepgram Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'Node.js not installed'`
!`npm list @deepgram/sdk 2>/dev/null | grep deepgram || echo '@deepgram/sdk not found'`
!`python3 --version 2>/dev/null || echo 'Python not installed'`

## Overview
Collect comprehensive debug information for Deepgram support tickets. Generates a sanitized bundle with environment info, API connectivity tests, audio analysis, request/response logs, and a minimal reproduction script. All API keys are automatically redacted.

## Prerequisites
- Deepgram API key configured
- `ffprobe` available for audio analysis (part of ffmpeg)
- Sample audio that reproduces the issue

## Instructions

### Step 1: Environment Collection Script

```bash
#!/bin/bash
set -euo pipefail
BUNDLE_DIR="deepgram-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

# System info
{
  echo "=== System ==="
  uname -a
  echo ""
  echo "=== Node.js ==="
  node --version 2>/dev/null || echo "Not installed"
  echo ""
  echo "=== @deepgram/sdk ==="
  npm list @deepgram/sdk 2>/dev/null || echo "Not installed"
  echo ""
  echo "=== Python ==="
  python3 --version 2>/dev/null || echo "Not installed"
  pip show deepgram-sdk 2>/dev/null || echo "Not installed"
} > "$BUNDLE_DIR/environment.txt"
```

### Step 2: API Connectivity Tests

```bash
# Test REST API
{
  echo "=== REST API Test ==="
  echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  echo "--- Project listing ---"
  curl -s -w "\nHTTP: %{http_code} | Time: %{time_total}s\n" \
    'https://api.deepgram.com/v1/projects' \
    -H "Authorization: Token $DEEPGRAM_API_KEY" 2>&1 | \
    sed "s/$DEEPGRAM_API_KEY/REDACTED/g"
  echo ""
  echo "--- Transcription test (Bueller sample) ---"
  curl -s -w "\nHTTP: %{http_code} | Time: %{time_total}s\n" \
    -X POST 'https://api.deepgram.com/v1/listen?model=nova-3&smart_format=true' \
    -H "Authorization: Token $DEEPGRAM_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"url":"https://static.deepgram.com/examples/Bueller-Life-moves-702702706.wav"}' 2>&1 | \
    sed "s/$DEEPGRAM_API_KEY/REDACTED/g"
  echo ""
  echo "--- WebSocket handshake test ---"
  curl -s -w "\nHTTP: %{http_code}\n" -o /dev/null \
    'https://api.deepgram.com/v1/listen' \
    -H "Authorization: Token $DEEPGRAM_API_KEY" \
    -H "Upgrade: websocket" 2>&1 | \
    sed "s/$DEEPGRAM_API_KEY/REDACTED/g"
} > "$BUNDLE_DIR/connectivity.txt"
```

### Step 3: Audio Analysis

```bash
# Analyze problem audio file (if provided)
analyze_audio() {
  local file="$1"
  local outfile="$BUNDLE_DIR/audio-analysis.txt"

  {
    echo "=== Audio Analysis: $(basename "$file") ==="
    echo "File size: $(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)"
    echo ""

    if command -v ffprobe &>/dev/null; then
      echo "--- FFprobe Output ---"
      ffprobe -v quiet -print_format json -show_format -show_streams "$file"
      echo ""

      echo "--- Key Properties ---"
      local codec=$(ffprobe -v quiet -show_entries stream=codec_name -of csv=p=0 "$file")
      local rate=$(ffprobe -v quiet -show_entries stream=sample_rate -of csv=p=0 "$file")
      local channels=$(ffprobe -v quiet -show_entries stream=channels -of csv=p=0 "$file")
      local duration=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$file")
      local bitdepth=$(ffprobe -v quiet -show_entries stream=bits_per_sample -of csv=p=0 "$file")

      echo "Codec: $codec"
      echo "Sample rate: $rate Hz"
      echo "Channels: $channels"
      echo "Bit depth: $bitdepth"
      echo "Duration: ${duration}s"
      echo ""

      # Check for common issues
      echo "--- Compatibility Check ---"
      [[ "$rate" -lt 8000 ]] && echo "WARNING: Sample rate below 8kHz minimum"
      [[ "$rate" -gt 48000 ]] && echo "WARNING: Sample rate above 48kHz — consider downsampling"
      [[ "$channels" -gt 2 ]] && echo "WARNING: >2 channels — Deepgram supports mono/stereo"
    else
      echo "ffprobe not available — install ffmpeg for audio analysis"
      echo ""
      echo "--- File header (hex) ---"
      xxd -l 16 "$file"
    fi
  } > "$outfile"
}
```

### Step 4: Request/Response Logger

```typescript
// Wrap Deepgram client to capture full request/response for debugging
import { createClient } from '@deepgram/sdk';
import { writeFileSync } from 'fs';

async function captureDebugRequest(audioSource: string | Buffer) {
  const client = createClient(process.env.DEEPGRAM_API_KEY!);
  const startTime = Date.now();

  try {
    const isUrl = typeof audioSource === 'string';
    const method = isUrl ? 'transcribeUrl' : 'transcribeFile';
    const source = isUrl ? { url: audioSource } : audioSource;
    const options = { model: 'nova-3' as const, smart_format: true };

    const { result, error } = isUrl
      ? await client.listen.prerecorded.transcribeUrl(source as any, options)
      : await client.listen.prerecorded.transcribeFile(source as any, options);

    const elapsed = Date.now() - startTime;

    const debugLog = {
      timestamp: new Date().toISOString(),
      method,
      options,
      elapsed_ms: elapsed,
      success: !error,
      error: error ? { message: error.message, status: (error as any).status } : null,
      result_summary: result ? {
        request_id: result.metadata?.request_id,
        duration: result.metadata?.duration,
        model: result.metadata?.model_info,
        transcript_length: result.results?.channels[0]?.alternatives[0]?.transcript?.length,
        confidence: result.results?.channels[0]?.alternatives[0]?.confidence,
      } : null,
    };

    writeFileSync('debug-request.json', JSON.stringify(debugLog, null, 2));
    console.log('Debug log written to debug-request.json');
    return debugLog;
  } catch (err: any) {
    const debugLog = {
      timestamp: new Date().toISOString(),
      elapsed_ms: Date.now() - startTime,
      error: { message: err.message, stack: err.stack },
    };
    writeFileSync('debug-request.json', JSON.stringify(debugLog, null, 2));
    throw err;
  }
}
```

### Step 5: Package and Sanitize Bundle

```bash
# Package everything (API keys already redacted in Step 2)
{
  echo "=== Deepgram Debug Bundle ==="
  echo "Created: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""
  echo "Issue Description: [DESCRIBE YOUR ISSUE HERE]"
  echo ""
  echo "Files:"
  echo "  environment.txt    - System and SDK versions"
  echo "  connectivity.txt   - API connectivity test results"
  echo "  audio-analysis.txt - Audio file properties (if provided)"
  echo "  debug-request.json - Request/response capture (if run)"
  echo ""
  echo "Attach this bundle to your support ticket at:"
  echo "  https://developers.deepgram.com/support"
} > "$BUNDLE_DIR/README.txt"

# Final sanitization pass — remove any leaked keys
find "$BUNDLE_DIR" -type f -exec sed -i "s/$DEEPGRAM_API_KEY/REDACTED/g" {} +

tar czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
echo "Bundle created: $BUNDLE_DIR.tar.gz"
```

### Step 6: Support Ticket Template

```
Subject: [Issue Type] — Brief Description

Environment:
- SDK: @deepgram/sdk v3.x.x
- Runtime: Node.js 20.x / Python 3.12
- OS: Ubuntu 22.04

Request ID: (from result.metadata.request_id)
Model: nova-3
Timestamp: 2026-03-22T12:00:00Z

Issue:
[Describe what you expected vs what happened]

Steps to Reproduce:
1. [Step 1]
2. [Step 2]
3. [Observe error]

Attachments:
- deepgram-debug-YYYYMMDD-HHMMSS.tar.gz
- Sample audio file (if shareable)
```

## Output
- `deepgram-debug-YYYYMMDD-HHMMSS.tar.gz` with sanitized diagnostics
- Environment and connectivity test results
- Audio file analysis with compatibility warnings
- Request/response debug capture
- Support ticket template

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| `ffprobe` not found | ffmpeg not installed | `apt install ffmpeg` or `brew install ffmpeg` |
| Connectivity test 401 | Key not exported | `export DEEPGRAM_API_KEY=your-key` |
| Empty audio analysis | File path wrong | Verify file exists and is readable |
| Tar fails | Permissions issue | Check write permissions in current directory |

## Resources
- [Deepgram Support Portal](https://developers.deepgram.com/support)
- [Deepgram Community](https://github.com/orgs/deepgram/discussions)
- [Status Page](https://status.deepgram.com)
