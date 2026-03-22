---
name: adobe-common-errors
description: |
  Diagnose and fix common Adobe API errors across Firefly Services, PDF Services,
  Photoshop API, and Adobe I/O Events.
  Use when encountering Adobe errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "adobe error", "fix adobe",
  "adobe not working", "debug adobe", "adobe 403", "adobe 429".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Common Errors

## Overview

Quick reference for the most common errors across Adobe APIs with real error messages, root causes, and verified fixes.

## Prerequisites

- Adobe SDK or API credentials configured
- Access to Adobe Developer Console (https://developer.adobe.com/console)
- Access to error logs or API responses

## Instructions

### Step 1: Identify the HTTP Status Code and Error Body

Adobe APIs return structured error responses:

```json
{
  "error_code": "403003",
  "message": "Api Key is invalid"
}
```

### Step 2: Match Error Below and Apply Fix

---

### Error 1: `401 Unauthorized` — Token Expired or Invalid

```
{"error":"invalid_token","error_description":"Could not match jwt signature to any of the bindings"}
```

**Cause:** Access token expired (24h TTL) or you are still using deprecated JWT credentials.

**Fix:**
```bash
# Regenerate OAuth Server-to-Server token
curl -X POST 'https://ims-na1.adobelogin.com/ims/token/v3' \
  -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}"

# If using JWT: migrate immediately — JWT reached EOL June 2025
# See: https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/migration
```

---

### Error 2: `403 Forbidden` — API Not Entitled

```
{"error_code":"403003","message":"Api Key is invalid"}
```

**Cause:** Your Developer Console project does not have the API added, or the product profile is missing.

**Fix:** Go to Developer Console > Project > Add API > Select the API > Assign product profile.

---

### Error 3: `429 Too Many Requests` — Rate Limited

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

**Cause:** Exceeded API rate limits. Adobe rate limits vary by API:
- Firefly: ~20 req/min on trial
- PDF Services: 500 transactions/month (free tier)
- Events Publishing: 3,000 req/5sec per api-key

**Fix:**
```typescript
// Honor the Retry-After header
const retryAfter = parseInt(response.headers.get('Retry-After') || '30');
await new Promise(r => setTimeout(r, retryAfter * 1000));
```

---

### Error 4: `400 Bad Request` — Firefly Content Policy

```
{"type":"INPUT_VALIDATION_ERROR","title":"prompt is not allowed by the content policy"}
```

**Cause:** Firefly prompt contains prohibited content (real people, trademarks, explicit content).

**Fix:** Remove prohibited terms. Firefly has guardrails against generating images of real people, brand logos, and copyrighted characters.

---

### Error 5: `400 InputValidationError` — Photoshop Storage URL

```
{"type":"InputValidationError","title":"input href is not a valid pre-signed URL"}
```

**Cause:** Photoshop/Lightroom APIs require pre-signed cloud storage URLs (S3, Azure Blob, Dropbox), not direct file uploads.

**Fix:**
```typescript
// Generate a pre-signed S3 URL for input
const inputUrl = await s3.getSignedUrl('getObject', {
  Bucket: 'my-bucket', Key: 'input.jpg', Expires: 3600
});
// Generate a pre-signed S3 URL for output
const outputUrl = await s3.getSignedUrl('putObject', {
  Bucket: 'my-bucket', Key: 'output.png', Expires: 3600
});
```

---

### Error 6: `DISQUALIFIED` — PDF Services Encrypted File

```
{"status":"failed","error":{"code":"DISQUALIFIED","message":"File is encrypted"}}
```

**Cause:** PDF is password-protected or has DRM restrictions.

**Fix:** Remove encryption before processing:
```bash
# Remove PDF password with qpdf
qpdf --decrypt --password=yourpassword input.pdf decrypted.pdf
```

---

### Error 7: `invalid_scope` — OAuth Scope Not Entitled

```
{"error":"invalid_scope","error_description":"scope openid,firefly_api not allowed"}
```

**Cause:** Your organization is not entitled to the requested API scope.

**Fix:** In Adobe Admin Console, ensure the product profile associated with your project includes the required API entitlements.

---

### Error 8: `ENOTFOUND` — DNS Resolution Failure

```
Error: getaddrinfo ENOTFOUND ims-na1.adobelogin.com
```

**Cause:** DNS resolution failure or network firewall blocking Adobe endpoints.

**Fix:**
```bash
# Test DNS resolution
nslookup ims-na1.adobelogin.com
nslookup firefly-api.adobe.io
nslookup image.adobe.io

# Ensure firewall allows outbound HTTPS to:
# - ims-na1.adobelogin.com (auth)
# - firefly-api.adobe.io (Firefly)
# - image.adobe.io (Photoshop/Lightroom)
# - pdf-services.adobe.io (PDF Services)
```

## Quick Diagnostic Commands

```bash
# Test OAuth token generation
curl -s -o /dev/null -w "%{http_code}" -X POST \
  'https://ims-na1.adobelogin.com/ims/token/v3' \
  -d "client_id=${ADOBE_CLIENT_ID}&client_secret=${ADOBE_CLIENT_SECRET}&grant_type=client_credentials&scope=${ADOBE_SCOPES}"

# Check Adobe service status
curl -s https://status.adobe.com/api/v1/incidents | python3 -m json.tool | head -20

# Verify which APIs your project has
# → Go to https://developer.adobe.com/console > Your Project > APIs
```

## Escalation Path

1. Collect evidence with `adobe-debug-bundle`
2. Check https://status.adobe.com for active incidents
3. Contact Adobe Support with request ID (from response headers: `x-request-id`)

## Resources

- [Adobe Status Page](https://status.adobe.com)
- [Adobe Developer Support](https://developer.adobe.com/support)
- [OAuth Implementation Guide](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/implementation)

## Next Steps

For comprehensive debugging, see `adobe-debug-bundle`.
