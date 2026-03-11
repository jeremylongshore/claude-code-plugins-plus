# Lokalise Common Errors - Implementation Guide

Detailed implementation reference for the lokalise-common-errors skill.

## Instructions

### Step 1: Identify the Error
Check error message, HTTP status code, and error code in logs or console.

### Step 2: Find Matching Error Below
Match your error to one of the documented cases.

### Step 3: Apply Solution
Follow the solution steps for your specific error.


## Quick Diagnostic Commands

```bash
# Check Lokalise API status
curl -s https://status.lokalise.com/api/v2/status.json | jq '.status.description'

# Test API connectivity
curl -I -X GET "https://api.lokalise.com/api2/system/health"

# Verify token and list projects
curl -X GET "https://api.lokalise.com/api2/projects" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" | jq '.projects[].name'

# Check rate limit headers
curl -v -X GET "https://api.lokalise.com/api2/projects" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN" 2>&1 | grep -i "x-ratelimit"
```


## Escalation Path
1. Collect evidence with `lokalise-debug-bundle`
2. Check [Lokalise Status Page](https://status.lokalise.com)
3. Search [Lokalise Community](https://community.lokalise.com)
4. Contact support via [support@lokalise.com](mailto:support@lokalise.com)


## Error Handling
### 401 Unauthorized - Invalid API Token
**Error Message:**
```json
{
  "error": {
    "code": 401,
    "message": "Invalid `X-Api-Token` header"
  }
}
```

**Cause:** API token is missing, expired, revoked, or incorrect.

**Solution:**
```bash
# Verify token is set
echo $LOKALISE_API_TOKEN | head -c 10

# Test token validity
curl -X GET "https://api.lokalise.com/api2/projects" \
  -H "X-Api-Token: $LOKALISE_API_TOKEN"

# Generate new token if needed:
# Profile Settings -> API tokens -> Generate new token
```

---

### 403 Forbidden - Insufficient Permissions
**Error Message:**
```json
{
  "error": {
    "code": 403,
    "message": "Forbidden"
  }
}
```

**Cause:** Token lacks required permissions for the operation.

**Solution:**
- Verify token has read-write access (not read-only)
- Check project permissions in Team settings
- Ensure you're a contributor with appropriate role

```typescript
// Check your permissions
const user = await lokaliseApi.teamUsers().list({ team_id: teamId });
console.log("User roles:", user.items.map(u => u.role));
```

---

### 404 Not Found - Resource Missing
**Error Message:**
```json
{
  "error": {
    "code": 404,
    "message": "Project not found"
  }
}
```

**Cause:** Project ID, key ID, or other resource doesn't exist.

**Solution:**
```bash
# List available projects
lokalise2 --token "$LOKALISE_API_TOKEN" project list

# Verify project ID format (should include hash)
# Correct: 123456789.abcdef12
# Wrong: 123456789
```

```typescript
// Get correct project ID
const projects = await lokaliseApi.projects().list();
projects.items.forEach(p => {
  console.log(`${p.name}: ${p.project_id}`);
});
```

---

### 429 Too Many Requests - Rate Limited
**Error Message:**
```json
{
  "error": {
    "code": 429,
    "message": "Too many requests"
  }
}
```

**Cause:** Exceeded 6 requests/second or 10 concurrent requests per project.

**Solution:**
```typescript
// Implement rate limiting
import PQueue from "p-queue";

const queue = new PQueue({
  concurrency: 5,
  interval: 1000,
  intervalCap: 5,
});

// Queue all requests
const result = await queue.add(() => lokaliseApi.keys().list({...}));
```

See `lokalise-rate-limits` for comprehensive handling.

---

### 400 Bad Request - Invalid Parameters
**Error Message:**
```json
{
  "error": {
    "code": 400,
    "message": "Invalid request"
  }
}
```

**Cause:** Missing required fields or invalid parameter values.

**Solution:**
```typescript
// Check required fields for key creation
const keys = await lokaliseApi.keys().create({
  project_id: projectId,  // Required
  keys: [{
    key_name: "my.key",   // Required
    platforms: ["web"],   // Required: web, ios, android, other
    // translations is optional
  }],
});
```

---

### 400 Key Limit Exceeded
**Error Message:**
```json
{
  "error": {
    "code": 400,
    "message": "Keys limit exceeded"
  }
}
```

**Cause:** Exceeded maximum keys per request (500 as of 2025).

**Solution:**
```typescript
// Batch keys in chunks of 500
async function createKeysInBatches(projectId: string, allKeys: any[]) {
  const batchSize = 500;
  const results = [];

  for (let i = 0; i < allKeys.length; i += batchSize) {
    const batch = allKeys.slice(i, i + batchSize);
    const result = await lokaliseApi.keys().create({
      project_id: projectId,
      keys: batch,
    });
    results.push(...result.items);

    // Respect rate limits
    await new Promise(r => setTimeout(r, 200));
  }

  return results;
}
```

---

### 413 Payload Too Large
**Error Message:**
```json
{
  "error": {
    "code": 413,
    "message": "Request entity too large"
  }
}
```

**Cause:** File upload exceeds size limit.

**Solution:**
- Split large files into smaller chunks
- Compress file before upload
- Use async upload with polling

```bash
# Check file size
ls -lh locales/en.json

# Split by namespace if needed
# Split monolithic file into:
# - common.json
# - features.json
# - errors.json
```

---

### Upload Process Failed
**Error Message:**
```json
{
  "status": "failed",
  "details": "..."
}
```

**Cause:** File format issues, invalid characters, or parsing errors.

**Solution:**
```bash
# Validate JSON
cat locales/en.json | jq . > /dev/null

# Check for BOM or encoding issues
file locales/en.json
# Should show: UTF-8 Unicode text

# Remove BOM if present
sed -i '1s/^\xEF\xBB\xBF//' locales/en.json
```
