# Step 2: Custom Error Classes

Deep-dive reference for the `figma-sdk-patterns` skill — extracted from the 'Step 2: Custom Error Classes' step of the workflow.

```typescript
// src/figma-errors.ts
export class FigmaApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`Figma API error ${status}: ${body}`);
    this.name = 'FigmaApiError';
  }
}

export class FigmaRateLimitError extends FigmaApiError {
  constructor(public retryAfterSeconds: number) {
    super(429, `Rate limited. Retry after ${retryAfterSeconds}s`);
    this.name = 'FigmaRateLimitError';
  }
}

export class FigmaAuthError extends FigmaApiError {
  constructor(message: string) {
    super(403, message);
    this.name = 'FigmaAuthError';
  }
}

export class FigmaNotFoundError extends FigmaApiError {
  constructor(path: string) {
    super(404, `Resource not found: ${path}`);
    this.name = 'FigmaNotFoundError';
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
