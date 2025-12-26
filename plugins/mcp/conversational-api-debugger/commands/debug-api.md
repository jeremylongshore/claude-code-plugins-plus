---
name: debug-api
description: Debug API failures using OpenAPI specs and HTTP logs
---
# Debug API Failures

Systematically debug REST API failures by analyzing OpenAPI specifications and HTTP request/response logs.

## Workflow

When the user requests API debugging, follow this comprehensive approach:

### Step 1: Load API Documentation

```
Use load_openapi to parse the OpenAPI spec:
- Accepts JSON or YAML format
- Extracts all endpoints, parameters, and expected responses
- Identifies authentication requirements
- Captures base URLs and server information

Example:
load_openapi({
  filePath: "/path/to/openapi.yaml",
  name: "my-api"
})
```

### Step 2: Ingest HTTP Logs

```
Use ingest_logs to import request/response data:
- Supports HAR (HTTP Archive) format from browser DevTools
- Accepts direct log arrays
- Automatically categorizes successful vs failed requests
- Calculates status code and method distributions

Example (HAR file):
ingest_logs({
  filePath: "/path/to/requests.har",
  format: "har"
})

Example (direct logs):
ingest_logs({
  logs: [
    {
      timestamp: "2025-10-10T12:00:00Z",
      method: "POST",
      url: "https://api.example.com/users",
      statusCode: 400,
      requestBody: { "name": "John" },
      responseBody: { "error": "Missing required field: email" }
    }
  ]
})
```

### Step 3: Analyze Failures

```
Use explain_failure to understand why requests failed:
- Identifies root causes based on HTTP status codes
- Compares actual behavior with OpenAPI spec expectations
- Suggests specific fixes
- Assesses severity (critical, high, medium, low)

Example:
explain_failure({
  logIndex: 0,  // Index from ingest_logs
  specName: "my-api"  // Compare against loaded spec
})
```

### Step 4: Generate Reproducible Tests

```
Use make_repro to create cURL commands:
- Generates executable cURL command
- Includes alternative formats (HTTPie, JavaScript fetch)
- Useful for documentation, bug reports, and testing

Example:
make_repro({
  logIndex: 0,
  includeHeaders: true,
  pretty: true  // Format for readability
})
```

## Common Debugging Scenarios

### Scenario 1: 400 Bad Request

1. **Load spec** to see expected request format
2. **Ingest logs** containing the failure
3. **Explain failure** to identify validation errors
4. **Make repro** to generate test command
5. **Fix request** based on schema requirements
6. **Test** using generated cURL command

### Scenario 2: 401 Unauthorized

1. **Load spec** to check authentication requirements
2. **Explain failure** on 401 response
3. **Verify** authentication headers in request
4. **Check** token expiration or permissions
5. **Make repro** with corrected auth headers

### Scenario 3: 500 Internal Server Error

1. **Ingest logs** to find pattern of 500 errors
2. **Explain failure** to assess criticality
3. **Make repro** for server team to reproduce
4. **Check** request payload for edge cases
5. **Monitor** server logs (not in scope of this tool)

### Scenario 4: Performance Issues

1. **Ingest logs** with duration data
2. **Analyze** distribution of response times
3. **Identify** slow endpoints
4. **Make repro** for performance testing

## Analysis Output

The debugging workflow produces:

### From explain_failure:
- **Severity**: critical | high | medium | low
- **Possible Causes**: List of likely root causes
- **Suggested Fixes**: Actionable remediation steps
- **Matching Endpoint**: Comparison with OpenAPI spec
- **Details**: Request/response bodies for inspection

### From make_repro:
- **cURL Command**: Copy-paste ready command
- **HTTPie Alternative**: Shorter syntax for quick tests
- **JavaScript fetch**: For integration into automated tests
- **Metadata**: Method, URL, headers, body presence

## Best Practices

1. **Always load the OpenAPI spec first** - Provides context for failure analysis
2. **Use HAR files** when possible - Most complete log format
3. **Include request/response bodies** - Critical for validation errors
4. **Compare with spec** - Catches mismatches between docs and implementation
5. **Generate repro commands** - Makes bug reports actionable
6. **Test fixes immediately** - Use generated cURL to verify

## Tips

- Export HAR from browser DevTools (Network tab → Right-click → Save as HAR)
- Use `pretty: true` for readable cURL commands (good for docs)
- Use `pretty: false` for one-liner cURL (good for scripts)
- Check response headers for hints (X-RateLimit-*, Retry-After, etc.)
- Look for patterns in multiple failures (same endpoint, same error)

## Example Usage

```
User: "My API is returning 400 errors, help me debug"

You:
1. First, do you have an OpenAPI spec? If yes, I'll load it.
2. How are you capturing HTTP logs? (HAR file, JSON logs, manual entry?)
3. Let me analyze the failures and suggest fixes.

[After receiving spec and logs]

I've loaded your API spec and found 5 failed requests:
- 3x POST /users → 400 (Missing required field: email)
- 2x GET /users/{id} → 404 (Invalid user ID format)

Let me explain the first failure...
[Uses explain_failure]

Here's a working cURL command to test the fix:
[Uses make_repro]
```

## Notes

- This tool focuses on client-side debugging (requests/responses)
- Server-side logs and profiling are out of scope
- For complex API issues, combine with other debugging tools
- Keep OpenAPI specs up-to-date for accurate analysis
