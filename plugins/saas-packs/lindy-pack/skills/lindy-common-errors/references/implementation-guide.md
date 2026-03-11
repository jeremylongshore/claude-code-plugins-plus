# Lindy Common Errors - Implementation Guide

# Lindy Common Errors

## Overview
Comprehensive guide to troubleshooting common Lindy AI errors and issues.

## Prerequisites
- Lindy SDK installed
- Access to logs and error messages
- Basic debugging skills

## Common Errors

### Authentication Errors

#### LINDY_AUTH_INVALID_KEY
```
Error: Invalid API key provided
Code: LINDY_AUTH_INVALID_KEY
```

**Causes:**
- Expired API key
- Incorrect key format
- Key from wrong environment

**Solutions:**
```bash
# Verify key is set
echo $LINDY_API_KEY

# Regenerate key in dashboard
# https://app.lindy.ai/settings/api-keys

# Test key
curl -H "Authorization: Bearer $LINDY_API_KEY" \
  https://api.lindy.ai/v1/users/me
```

### Rate Limit Errors

#### LINDY_RATE_LIMITED
```
Error: Rate limit exceeded
Code: LINDY_RATE_LIMITED
Retry-After: 60
```

**Causes:**
- Too many API requests
- Concurrent agent runs exceeded
- Burst limit reached

**Solutions:**
```typescript
// Implement exponential backoff
async function withBackoff<T>(fn: () => Promise<T>): Promise<T> {
  for (let i = 0; i < 5; i++) {
    try {
      return await fn();
    } catch (e: any) {
      if (e.code === 'LINDY_RATE_LIMITED') {
        const delay = Math.pow(2, i) * 1000;
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw e;
    }
  }
  throw new Error('Max retries exceeded');
}
```

### Agent Errors

#### LINDY_AGENT_NOT_FOUND
```
Error: Agent not found
Code: LINDY_AGENT_NOT_FOUND
```

**Solutions:**
```typescript
// Verify agent exists
const agents = await lindy.agents.list();
const exists = agents.some(a => a.id === agentId);

// Check environment (dev vs prod)
console.log('Environment:', process.env.LINDY_ENVIRONMENT);
```

#### LINDY_AGENT_TIMEOUT
```
Error: Agent execution timed out
Code: LINDY_AGENT_TIMEOUT
```

**Solutions:**
```typescript
// Increase timeout
const result = await lindy.agents.run(agentId, {
  input,
  timeout: 120000, // 2 minutes
});

// Use streaming for long tasks
const stream = await lindy.agents.runStream(agentId, { input });
```

### Tool Errors

#### LINDY_TOOL_FAILED
```
Error: Tool execution failed
Code: LINDY_TOOL_FAILED
Tool: email
```

**Solutions:**
```typescript
// Check tool configuration
const agent = await lindy.agents.get(agentId);
console.log('Tools:', agent.tools);

// Verify tool credentials
await lindy.tools.test('email');
```

## Debugging Checklist

```markdown
[ ] API key is valid and not expired
[ ] Correct environment (dev/staging/prod)
[ ] Agent ID exists and is accessible
[ ] Rate limits not exceeded
[ ] Network connectivity to api.lindy.ai
[ ] Required tools are configured
[ ] Timeout is sufficient for task
```

## Error Handling
| Error Code | HTTP Status | Retry? |
|------------|-------------|--------|
| LINDY_AUTH_INVALID_KEY | 401 | No |
| LINDY_RATE_LIMITED | 429 | Yes |
| LINDY_AGENT_NOT_FOUND | 404 | No |
| LINDY_AGENT_TIMEOUT | 504 | Yes |
| LINDY_TOOL_FAILED | 500 | Maybe |

## Resources
- [Lindy Error Reference](https://docs.lindy.ai/errors)
- [Status Page](https://status.lindy.ai)
- [Support](https://support.lindy.ai)

## Next Steps
Proceed to `lindy-debug-bundle` for comprehensive debugging.
