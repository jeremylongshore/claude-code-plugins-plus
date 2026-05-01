---
name: api-testing
description: "Use when testing HTTP endpoints, probing URLs for status and headers, or running declarative API test suites from plain text files"
allowed-tools: [Bash(hurl*), Bash(httpx*), Read, Write, Glob]
version: 1.0.0
author: ykotik
license: MIT
---

# API Testing

## When to Use
- Testing REST API endpoints for correct responses
- Writing declarative, repeatable HTTP test suites
- Chaining HTTP requests (authenticate → create → verify)
- Probing multiple URLs for availability, status codes, or headers
- Validating response bodies, headers, and status codes with assertions

## Tools

| Tool | Purpose | Structured output |
|------|---------|-------------------|
| **Hurl** | Declarative HTTP testing from plain text `.hurl` files | `--json` for JSON report |
| **httpx** | Fast HTTP probing toolkit (ProjectDiscovery) | `-json` for JSON output |

## Patterns

### Hurl: Simple GET with status assertion
Create a `.hurl` file:
```hurl
GET http://localhost:3000/api/health
HTTP 200
[Asserts]
jsonpath "$.status" == "ok"
```
Run it:
```bash
hurl health.hurl
```

### Hurl: POST with JSON body and response validation
```hurl
POST http://localhost:3000/api/users
Content-Type: application/json
{
  "name": "Alice",
  "email": "alice@example.com"
}
HTTP 201
[Asserts]
jsonpath "$.id" isInteger
jsonpath "$.name" == "Alice"
```

### Hurl: Chained requests (auth → create → verify)
```hurl
# Step 1: Login
POST http://localhost:3000/api/auth/login
Content-Type: application/json
{
  "email": "admin@example.com",
  "password": "secret"
}
HTTP 200
[Captures]
token: jsonpath "$.token"

# Step 2: Create resource with token
POST http://localhost:3000/api/items
Authorization: Bearer {{token}}
Content-Type: application/json
{
  "title": "New Item"
}
HTTP 201
[Captures]
item_id: jsonpath "$.id"

# Step 3: Verify resource exists
GET http://localhost:3000/api/items/{{item_id}}
Authorization: Bearer {{token}}
HTTP 200
[Asserts]
jsonpath "$.title" == "New Item"
```

### Hurl: Run test suite with JSON report
```bash
hurl --test --report-json report/ tests/*.hurl
```

### Hurl: Use variables from command line
```bash
hurl --variable host=https://staging.example.com --variable token=abc123 tests/api.hurl
```

### httpx: Probe a list of URLs for status codes
```bash
echo -e "https://example.com\nhttps://httpbin.org\nhttps://nonexistent.invalid" | httpx -silent -status-code
```

### httpx: Probe with full JSON output (status, title, tech)
```bash
echo "https://example.com" | httpx -json -title -tech-detect -status-code
```

### httpx: Check specific ports across hosts
```bash
echo -e "192.168.1.1\n192.168.1.2" | httpx -ports 80,443,8080 -status-code
```

### httpx: Follow redirects and show final URL
```bash
echo "http://github.com" | httpx -follow-redirects -location -status-code
```

## Pipelines

### Hurl test suite → summarize failures
```bash
hurl --test --report-json report/ tests/*.hurl 2>&1; jq '[.[] | select(.success == false) | {file: .filename, errors: [.entries[] | select(.errors | length > 0) | .errors]}]' report/*.json
```
Each stage: Hurl runs all tests and writes JSON reports, jq filters to failures and extracts error details.

### Discover endpoints with Katana → probe with httpx
```bash
katana -u https://example.com -silent -d 2 | httpx -silent -status-code -json
```
Each stage: Katana crawls and discovers URLs, httpx probes each for status and metadata.

## Prefer Over
- Prefer **Hurl** over curl scripts for multi-step API testing — declarative syntax with built-in assertions, no bash scripting needed
- Prefer **Hurl** over Postman/Bruno for CI-friendly test suites — plain text files, no GUI dependency
- Prefer **httpx** over curl loops for probing many URLs — concurrent, structured output, built for scale

## Do NOT Use When
- Need full browser rendering or JavaScript execution — use web-crawling skill (Playwright)
- Building a long-running API client or SDK — write code instead
- Testing WebSocket or gRPC endpoints — use specialized tools (wscat, grpcurl)
- Single ad-hoc curl request — just use `curl` directly
