# Step 1: Circuit Breaker

Deep-dive reference for the `figma-reliability-patterns` skill — extracted from the 'Step 1: Circuit Breaker' step of the workflow.

```typescript
// Prevent cascading failures when Figma is down
class FigmaCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private threshold = 5,        // Open after 5 failures
    private resetTimeMs = 30_000  // Try again after 30s
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.resetTimeMs) {
        this.state = 'half-open';
        console.log('[figma-circuit] State: half-open (testing recovery)');
      } else {
        throw new Error('Figma circuit breaker is OPEN -- failing fast');
      }
    }

    try {
      const result = await fn();
      if (this.state === 'half-open') {
        this.state = 'closed';
        this.failures = 0;
        console.log('[figma-circuit] State: closed (recovered)');
      }
      return result;
    } catch (error) {
      this.failures++;
      this.lastFailure = Date.now();

      if (this.failures >= this.threshold) {
        this.state = 'open';
        console.warn(`[figma-circuit] State: OPEN after ${this.failures} failures`);
      }
      throw error;
    }
  }

  getState() { return this.state; }
}

const figmaBreaker = new FigmaCircuitBreaker();

// Usage
async function safeFigmaCall<T>(fn: () => Promise<T>): Promise<T> {
  return figmaBreaker.execute(fn);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
