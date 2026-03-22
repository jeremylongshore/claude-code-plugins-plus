---
name: palantir-common-errors
description: |
  Diagnose and fix Palantir Foundry common errors and API exceptions.
  Use when encountering Foundry errors, debugging failed API calls,
  or troubleshooting transform build failures.
  Trigger with phrases like "palantir error", "fix palantir",
  "foundry not working", "debug foundry", "palantir 401 403".
allowed-tools: Read, Grep, Bash(curl:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, debugging, errors]
compatible-with: claude-code, codex, openclaw
---

# Palantir Common Errors

## Overview
Quick reference for the top 10 most common Foundry API and transform errors with copy-paste solutions.

## Prerequisites
- `foundry-platform-sdk` installed
- API credentials configured
- Access to Foundry build logs or application logs

## Instructions

### Error 1: 401 Unauthorized — Invalid or Expired Token
```
foundry.ApiError: 401 Unauthorized — The provided token is invalid or expired.
```
**Fix:**
```python
# Regenerate token in Developer Console
# Settings > Tokens > Generate new personal access token
# Or re-authenticate with OAuth2:
auth = foundry.ConfidentialClientAuth(
    client_id=os.environ["FOUNDRY_CLIENT_ID"],
    client_secret=os.environ["FOUNDRY_CLIENT_SECRET"],
    hostname=os.environ["FOUNDRY_HOSTNAME"],
    scopes=["api:read-data"],
)
auth.sign_in_as_service_user()  # Gets a fresh token
```

### Error 2: 403 Forbidden — Insufficient Scopes
```
foundry.ApiError: 403 Forbidden — Missing required scope: api:ontology-read
```
**Fix:** Add missing scopes in Developer Console > Your App > Scopes. Common scopes:
- `api:read-data` — read datasets
- `api:write-data` — write datasets
- `api:ontology-read` — read Ontology objects
- `api:ontology-write` — apply actions

### Error 3: ObjectTypeNotFound
```
foundry.ApiError: 404 ObjectTypeNotFound — Object type 'employee' not found
```
**Fix:** Object type names are `camelCase` API names, not display names. Check Ontology Manager:
```python
# List all object types to find the correct api_name
for ot in client.ontologies.ObjectType.list(ontology="my-company"):
    print(f"  {ot.api_name} (display: {ot.display_name})")
```

### Error 4: DatasetNotFound
```
foundry.ApiError: 404 DatasetNotFound — Dataset not found or you do not have access
```
**Fix:** Verify the dataset RID (right-click dataset in Foundry UI > Copy RID). Ensure your service user has Viewer/Editor role on the project.

### Error 5: Transform Build AnalysisException
```
pyspark.sql.utils.AnalysisException: cannot resolve 'fullname' given columns [fullName, department]
```
**Fix:** Spark column names are case-sensitive. Print columns to debug:
```python
@transform_df(Output("/out"), data=Input("/in"))
def my_transform(data):
    print(data.columns)  # Check actual column names
    return data.select("fullName")  # Use exact casing
```

### Error 6: OutOfMemoryError in Transform Builds
```
java.lang.OutOfMemoryError: Java heap space
```
**Fix:** Add `@configure` with a larger memory profile:
```python
from transforms.api import configure
@configure(profile=["DRIVER_MEMORY_LARGE"])  # 16GB
@transform_df(Output("/out"), data=Input("/in"))
def heavy_transform(data):
    return data.groupBy("region").agg({"amount": "sum"})
```

### Error 7: ActionValidationFailed
```
foundry.ApiError: ActionValidationFailed — Parameter 'salary' must be positive
```
**Fix:** Read the validation messages for specific constraint violations:
```python
result = client.ontologies.Action.apply(
    ontology="my-company",
    action_type="updateSalary",
    parameters={"employeeId": "EMP-001", "salary": 150000},
)
if result.validation != "VALID":
    for msg in result.validation_messages:
        print(f"  Validation error: {msg}")
```

### Error 8: ConnectionError / SSL Error
```
requests.exceptions.SSLError: SSL certificate verify failed
```
**Fix:** Common behind corporate proxies. Set the CA bundle:
```bash
export REQUESTS_CA_BUNDLE=/path/to/corporate-ca-bundle.crt
# Or for development only (NOT production):
export FOUNDRY_SSL_VERIFY=false
```

### Error 9: Rate Limit 429
```
foundry.ApiError: 429 Too Many Requests — Rate limit exceeded
```
**Fix:** See `palantir-rate-limits` for full implementation. Quick fix:
```python
import time
time.sleep(int(response.headers.get("Retry-After", 5)))
```

### Error 10: Circular Dependency in Transforms
```
Build failed: Circular dependency detected between datasets
```
**Fix:** Dataset A's transform reads from B, and B reads from A. Break the cycle by introducing an intermediate dataset or restructuring the pipeline DAG.

## Output
- Identified error from Foundry API response or build logs
- Applied targeted fix
- Verified resolution with successful API call or build

## Error Handling
| HTTP Code | Meaning | Retryable |
|-----------|---------|-----------|
| 400 | Bad Request (invalid params) | No — fix request |
| 401 | Token expired/invalid | No — re-authenticate |
| 403 | Missing scopes | No — update app scopes |
| 404 | Resource not found | No — fix identifier |
| 429 | Rate limited | Yes — wait and retry |
| 500/502/503 | Server error | Yes — retry with backoff |

## Resources
- [Foundry API Reference](https://www.palantir.com/docs/foundry/api/general/overview/introduction)
- [Transforms Python API](https://www.palantir.com/docs/foundry/transforms-python/transforms-python-api)

## Next Steps
For deeper debugging, see `palantir-debug-bundle`.
