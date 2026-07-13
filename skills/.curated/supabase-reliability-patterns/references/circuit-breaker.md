# Circuit Breaker

## Circuit Breaker

```typescript
import CircuitBreaker from 'opossum';

const supabaseBreaker = new CircuitBreaker(
  async (operation: () => Promise<any>) => operation(),
  {
    timeout: 30000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000,
    volumeThreshold: 10,
  }
);

// Events
supabaseBreaker.on('open', () => {
  console.warn('Supabase circuit OPEN - requests failing fast');
  alertOps('Supabase circuit breaker opened');
});

supabaseBreaker.on('halfOpen', () => {
  console.info('Supabase circuit HALF-OPEN - testing recovery');
});

supabaseBreaker.on('close', () => {
  console.info('Supabase circuit CLOSED - normal operation');
});

// Usage
async function safeSupabaseCall<T>(fn: () => Promise<T>): Promise<T> {
  return supabaseBreaker.fire(fn);
}
```
