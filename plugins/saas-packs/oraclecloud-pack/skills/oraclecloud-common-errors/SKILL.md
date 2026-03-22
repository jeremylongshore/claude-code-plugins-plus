---
name: oraclecloud-common-errors
description: |
  Diagnose and fix Oracle Cloud common errors.
  Trigger: "oraclecloud error", "fix oraclecloud", "debug oraclecloud".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, oraclecloud, infrastructure]
compatible-with: claude-code
---

# Oracle Cloud Common Errors

## Overview
Quick reference for Oracle Cloud API errors with solutions.

### 401 — Not Authenticated
**Fix:** Check `~/.oci/config` has valid key and fingerprint.

### 404 — Not Found
**Fix:** Verify OCID is correct and resource exists in compartment.

### 429 — Too Many Requests
**Fix:** OCI API: varies by service. Implement backoff.

### 500 — Internal Error
**Fix:** Check OCI status at https://ocistatus.oraclecloud.com.

### ServiceError: NotAuthorizedOrNotFound
**Fix:** IAM policy missing. Add required policy statement.

## Quick Diagnostic
```bash
# Check API connectivity
curl -s -w "\nHTTP %{http_code}" https://iaas.us-phoenix-1.oraclecloud.com/20160918/health 2>/dev/null || echo "Endpoint check needed"
echo $OCI_CONFIG_FILE | head -c 10
```

## Resources
- [Oracle Cloud Docs](https://docs.oracle.com/en-us/iaas/api/)

## Next Steps
See `oraclecloud-debug-bundle`.
