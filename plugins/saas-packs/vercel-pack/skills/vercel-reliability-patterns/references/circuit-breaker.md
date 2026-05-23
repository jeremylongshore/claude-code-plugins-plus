# Circuit Breaker

## Circuit Breaker

```typescript
import CircuitBreaker from 'opossum';

const vercelBreaker = new CircuitBreaker(
  async (operation: () => Promise<any>) => operation(),
  {
    timeout: 10000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000,
    volumeThreshold: 10,
  }
);

// Events
vercelBreaker.on('open', () => {
  console.warn('Vercel circuit OPEN - requests failing fast');
  alertOps('Vercel circuit breaker opened');
});

vercelBreaker.on('halfOpen', () => {
  console.info('Vercel circuit HALF-OPEN - testing recovery');
});

vercelBreaker.on('close', () => {
  console.info('Vercel circuit CLOSED - normal operation');
});

// Usage
async function safeVercelCall<T>(fn: () => Promise<T>): Promise<T> {
  return vercelBreaker.fire(fn);
}
```
