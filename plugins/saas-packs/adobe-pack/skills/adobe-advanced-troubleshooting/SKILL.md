---
name: adobe-advanced-troubleshooting
description: |
  Apply advanced debugging techniques for Adobe API issues: IMS token
  introspection, Firefly job failure analysis, PDF Services error
  codes, and network-layer diagnostics for Adobe endpoints.
  Trigger with phrases like "adobe hard bug", "adobe mystery error",
  "adobe impossible to debug", "difficult adobe issue", "adobe deep debug".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*), Bash(tcpdump:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Advanced Troubleshooting

## Overview

Deep debugging techniques for complex Adobe API issues that resist standard troubleshooting: IMS token problems, Firefly async job failures, PDF Services edge cases, and network-layer diagnostics.

## Prerequisites

- Access to production logs and metrics
- `curl` with verbose mode for HTTP debugging
- Understanding of OAuth 2.0 token flows
- Network capture tools (`tcpdump`, `openssl s_client`)

## Instructions

### Technique 1: IMS Token Introspection

When auth issues occur, decode the access token to check claims:

```bash
# Adobe IMS tokens are JWTs — decode the payload (middle segment)
TOKEN=$(curl -s -X POST 'https://ims-na1.adobelogin.com/ims/token/v3' \
  -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}" | jq -r '.access_token')

# Decode JWT payload (base64url-decode the middle segment)
echo "$TOKEN" | cut -d. -f2 | tr '_-' '/+' | base64 -d 2>/dev/null | python3 -m json.tool

# Look for:
# - "exp": expiration timestamp (is it expired?)
# - "iss": should be "ims-na1.adobelogin.com"
# - "as": scopes granted (do they match what you requested?)
# - "client_id": verify it matches your ADOBE_CLIENT_ID
```

### Technique 2: Verbose HTTP Request Tracing

```bash
# Full HTTP trace against Firefly API
curl -v -X POST 'https://firefly-api.adobe.io/v3/images/generate' \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "x-api-key: ${ADOBE_CLIENT_ID}" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","n":1,"size":{"width":512,"height":512}}' 2>&1 | tee firefly-debug.log

# Check for:
# - TLS handshake issues (look for SSL/TLS lines)
# - Request headers actually sent
# - Response headers (Retry-After, x-request-id, x-adobe-*)
# - Response body with error details
```

### Technique 3: Firefly Async Job Failure Analysis

```typescript
// When async Firefly jobs fail, the status endpoint returns error details
async function diagnoseFireflyJob(jobId: string, statusUrl: string) {
  const token = await getAccessToken();

  const response = await fetch(statusUrl, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'x-api-key': process.env.ADOBE_CLIENT_ID!,
    },
  });

  const status = await response.json();

  console.log('=== Firefly Job Diagnosis ===');
  console.log('Job ID:', jobId);
  console.log('Status:', status.status);

  if (status.status === 'failed') {
    console.log('Error code:', status.error?.code);
    console.log('Error message:', status.error?.message);
    console.log('Error details:', JSON.stringify(status.error?.details, null, 2));

    // Common failure reasons:
    // - "content_policy": prompt violated guidelines
    // - "input_validation": invalid parameters
    // - "internal_error": Adobe server issue (retry)
    // - "timeout": job took too long (simplify prompt)
  }

  // Log all response headers for Adobe support
  console.log('Response headers:', Object.fromEntries(response.headers.entries()));
}
```

### Technique 4: PDF Services Error Code Mapping

```typescript
// src/adobe/pdf-error-map.ts
// Comprehensive PDF Services error codes and recovery actions

const PDF_ERROR_MAP: Record<string, { cause: string; action: string; retryable: boolean }> = {
  'DISQUALIFIED':      { cause: 'File is encrypted/password-protected', action: 'Decrypt PDF first', retryable: false },
  'BAD_PDF':           { cause: 'Corrupted or invalid PDF', action: 'Validate with pdfinfo/pdftk', retryable: false },
  'BAD_PDF_CONTENT':   { cause: 'PDF content is malformed', action: 'Re-export from source', retryable: false },
  'UNSUPPORTED_MEDIA_TYPE': { cause: 'Wrong file format for operation', action: 'Check MimeType matches file', retryable: false },
  'FILE_SIZE_EXCEEDED': { cause: 'File exceeds size limit', action: 'Compress or split PDF', retryable: false },
  'PAGE_LIMIT_EXCEEDED': { cause: 'Too many pages for operation', action: 'Split into smaller PDFs', retryable: false },
  'QUOTA_EXCEEDED':    { cause: 'Monthly transaction limit hit', action: 'Upgrade plan or wait for reset', retryable: false },
  'INTERNAL_ERROR':    { cause: 'Adobe server error', action: 'Retry with backoff', retryable: true },
  'TIMEOUT':           { cause: 'Processing timeout', action: 'Try smaller file or fewer pages', retryable: true },
};

export function diagnosePdfError(errorCode: string): string {
  const info = PDF_ERROR_MAP[errorCode];
  if (!info) return `Unknown PDF Services error: ${errorCode}`;
  return `${errorCode}: ${info.cause}\nAction: ${info.action}\nRetryable: ${info.retryable}`;
}
```

### Technique 5: Layer-by-Layer Isolation

```bash
#!/bin/bash
# adobe-layer-test.sh — Test each network layer independently

echo "=== Layer 1: DNS Resolution ==="
nslookup ims-na1.adobelogin.com
nslookup firefly-api.adobe.io
nslookup image.adobe.io

echo ""
echo "=== Layer 2: TCP Connectivity ==="
for host in ims-na1.adobelogin.com firefly-api.adobe.io image.adobe.io; do
  timeout 5 bash -c "echo > /dev/tcp/$host/443" 2>/dev/null && echo "$host:443 OPEN" || echo "$host:443 BLOCKED"
done

echo ""
echo "=== Layer 3: TLS Handshake ==="
for host in ims-na1.adobelogin.com firefly-api.adobe.io; do
  echo | openssl s_client -connect "$host:443" -servername "$host" 2>/dev/null | grep -E "subject|issuer|Verify return"
done

echo ""
echo "=== Layer 4: IMS Authentication ==="
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
  'https://ims-na1.adobelogin.com/ims/token/v3' \
  -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}")
echo "IMS Token: HTTP $HTTP_CODE"

echo ""
echo "=== Layer 5: API Endpoint ==="
if [ "$HTTP_CODE" = "200" ]; then
  TOKEN=$(curl -s -X POST 'https://ims-na1.adobelogin.com/ims/token/v3' \
    -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
  API_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST \
    'https://firefly-api.adobe.io/v3/images/generate' \
    -H "Authorization: Bearer $TOKEN" \
    -H "x-api-key: $ADOBE_CLIENT_ID" \
    -H "Content-Type: application/json" \
    -d '{"prompt":"test","n":1,"size":{"width":512,"height":512}}')
  echo "Firefly API: HTTP $API_CODE"
fi
```

### Technique 6: Extract x-request-id for Adobe Support

```typescript
// Always capture x-request-id from Adobe responses for support escalation
async function debugAdobeCall(url: string, options: RequestInit) {
  const response = await fetch(url, options);

  const debugInfo = {
    url,
    status: response.status,
    requestId: response.headers.get('x-request-id'),
    retryAfter: response.headers.get('Retry-After'),
    contentType: response.headers.get('content-type'),
    date: response.headers.get('date'),
  };

  if (!response.ok) {
    const body = await response.text();
    console.error('Adobe API Error:', { ...debugInfo, body: body.slice(0, 500) });
    // Include x-request-id in support ticket for Adobe to trace the request
  }

  return { response, debugInfo };
}
```

## Support Escalation Template

```
Adobe Support Ticket

Severity: P[1-4]
x-request-id: [from response header]
Timestamp: [ISO 8601]
Client ID: [first 8 chars only]
API: [Firefly / PDF Services / Photoshop]
Endpoint: [full URL]
HTTP Status: [status code]

Issue Summary: [1-2 sentences]

Steps to Reproduce:
1. [Step]
2. [Step]

Evidence:
- Layer test results attached
- Verbose curl output attached
- JWT token claims (non-sensitive fields only)

Workarounds Attempted:
1. [What you tried] - [Result]
```

## Output

- IMS token decoded and claims inspected
- HTTP request/response fully traced
- Error codes mapped to recovery actions
- Network layers tested independently
- Support escalation with x-request-id

## Resources

- [Adobe Developer Support](https://developer.adobe.com/support)
- [Adobe Status Page](https://status.adobe.com)
- [Firefly API Reference](https://developer.adobe.com/firefly-services/docs/firefly-api/api/)
- [PDF Services Error Reference](https://developer.adobe.com/document-services/docs/overview/pdf-services-api/howtos/)

## Next Steps

For load testing, see `adobe-load-scale`.
