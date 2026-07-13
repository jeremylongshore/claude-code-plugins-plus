# Step 3: Rate Limit Edge Cases

Deep-dive reference for the `figma-advanced-troubleshooting` skill — extracted from the 'Step 3: Rate Limit Edge Cases' step of the workflow.

```typescript
// Problem: Figma rate limits are per-user, per-minute, but the exact
// limit is not published and varies by plan tier and seat type.

// Diagnostic: measure your actual limit by counting successful requests
async function measureRateLimit(token: string): Promise<{
  requestsMade: number;
  firstRateLimitAt: number | null;
  retryAfter: number | null;
}> {
  let count = 0;
  let rateLimitAt: number | null = null;
  let retryAfter: number | null = null;

  // Make requests until rate limited (use a read-only endpoint)
  while (count < 200) {
    const res = await fetch('https://api.figma.com/v1/me', {
      headers: { 'X-Figma-Token': token },
    });

    if (res.status === 429) {
      rateLimitAt = count;
      retryAfter = parseInt(res.headers.get('Retry-After') || '0');
      break;
    }

    count++;
    // Small delay to avoid instant burst
    await new Promise(r => setTimeout(r, 100));
  }

  return { requestsMade: count, firstRateLimitAt: rateLimitAt, retryAfter };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
