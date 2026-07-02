# Step 5: Support Escalation Template

Deep-dive reference for the `figma-advanced-troubleshooting` skill — extracted from the 'Step 5: Support Escalation Template' step of the workflow.

```markdown
## Figma API Support Request

**Account email:** [your-email]
**Plan tier:** [Starter/Professional/Organization/Enterprise]
**Endpoint:** [e.g., GET /v1/files/:key]
**File key:** [file key, not sensitive]

### Issue Description
[1-2 sentences describing the problem]

### Reproduction Steps
1. Call `GET https://api.figma.com/v1/files/FILE_KEY?depth=1`
2. Observe: [expected vs actual behavior]

### Diagnostic Data
- HTTP status: [status code]
- Response headers: [relevant headers, especially rate limit]
- Response time: [from curl timing]
- Frequency: [every time / intermittent / specific conditions]

### Request/Response (redacted)
```

curl -v -H "X-Figma-Token: [REDACTED]" \
  "https://api.figma.com/v1/files/FILE_KEY?depth=1"

HTTP/2 [status]
x-figma-rate-limit-type: [value]
retry-after: [value]

```

### Environment
- Node.js: [version]
- OS: [os]
- Region: [your server region]
- Behind proxy: [yes/no]
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
