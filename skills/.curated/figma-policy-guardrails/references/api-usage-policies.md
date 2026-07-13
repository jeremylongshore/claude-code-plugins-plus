# Step 3: API Usage Policies

Deep-dive reference for the `figma-policy-guardrails` skill — extracted from the 'Step 3: API Usage Policies' step of the workflow.

```typescript
// Runtime guardrails for Figma API usage

// Policy 1: No full-file fetches without justification
function validateFigmaRequest(path: string) {
  // Block unoptimized full file fetches
  if (path.match(/\/v1\/files\/[^/]+$/) && !path.includes('depth=')) {
    console.warn(
      '[figma-policy] Full file fetch without depth parameter. ' +
      'Use ?depth=1 or /nodes endpoint for better performance.'
    );
  }

  // Block deprecated scope indicator
  if (path.includes('files:read')) {
    throw new Error(
      '[figma-policy] files:read scope is deprecated. ' +
      'Use file_content:read instead.'
    );
  }
}

// Policy 2: Enforce timeout on all Figma calls
function validateTimeout(options: RequestInit) {
  if (!options.signal) {
    console.warn(
      '[figma-policy] Figma request without AbortSignal. ' +
      'Use AbortSignal.timeout() to prevent hung requests.'
    );
  }
}

// Policy 3: Rate limit safety margin
const MAX_REQUESTS_PER_MINUTE = 25; // Conservative limit
let requestsThisMinute = 0;
let minuteStart = Date.now();

function enforceRatePolicy() {
  if (Date.now() - minuteStart > 60_000) {
    requestsThisMinute = 0;
    minuteStart = Date.now();
  }

  requestsThisMinute++;
  if (requestsThisMinute > MAX_REQUESTS_PER_MINUTE) {
    throw new Error(
      `[figma-policy] Rate limit safety: ${requestsThisMinute} requests/min ` +
      `exceeds policy limit of ${MAX_REQUESTS_PER_MINUTE}`
    );
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
