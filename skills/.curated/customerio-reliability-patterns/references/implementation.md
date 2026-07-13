# Customer.io Reliability Patterns - Implementation Details

## Configuration

### Circuit Breaker for Customer.io

```typescript
import CircuitBreaker from 'opossum';

const cioBreaker = new CircuitBreaker(
  async (userId: string, event: string, data: any) => {
    return cio.track(userId, { name: event, data });
  },
  {
    timeout: 5000,
    errorThresholdPercentage: 50,
    resetTimeout: 30000,
    volumeThreshold: 10,
  }
);

cioBreaker.on('open', () => {
  console.warn('[CIO] Circuit breaker OPEN');
  metrics.increment('cio.circuit.open');
});

cioBreaker.fallback(async (userId, event, data) => {
  await fallbackQueue.add({ userId, event, data });
  return { queued: true };
});
```

## Advanced Patterns

### Retry with Dead Letter Queue

```typescript
class CioReliableTracker {
  private maxRetries = 3;

  async track(userId: string, event: string, data: any, attempt = 0): Promise<void> {
    try {
      await cioBreaker.fire(userId, event, data);
    } catch (err) {
      if (attempt >= this.maxRetries) {
        await this.deadLetter({ userId, event, data, error: String(err), attempts: attempt });
        return;
      }
      const delay = Math.pow(2, attempt) * 1000;
      await new Promise((r) => setTimeout(r, delay));
      return this.track(userId, event, data, attempt + 1);
    }
  }

  private async deadLetter(item: any) {
    console.error('[CIO] Dead letter:', item);
    await db.insert('cio_dead_letter', { ...item, created_at: new Date() });
  }
}
```

### Write-Ahead Log for Critical Events

```typescript
async function reliableTrack(userId: string, event: string, data: any) {
  // 1. Write to local WAL first
  const walId = await wal.append({ userId, event, data, status: 'pending' });

  // 2. Attempt delivery
  try {
    await cio.track(userId, { name: event, data });
    await wal.markComplete(walId);
  } catch (err) {
    await wal.markFailed(walId, String(err));
    // WAL replay worker will retry later
  }
}

// Background worker replays failed WAL entries
async function replayWal() {
  const pending = await wal.getPending({ limit: 100 });
  for (const entry of pending) {
    try {
      await cio.track(entry.userId, { name: entry.event, data: entry.data });
      await wal.markComplete(entry.id);
    } catch {
      await wal.incrementRetry(entry.id);
    }
  }
}
```

### Graceful Degradation Modes

```typescript
enum DegradationLevel {
  FULL = 'full',
  ESSENTIAL_ONLY = 'essential_only',
  DISABLED = 'disabled',
}

const ESSENTIAL_EVENTS = new Set(['signup', 'purchase', 'subscription_changed']);

function shouldSendEvent(event: string, level: DegradationLevel): boolean {
  switch (level) {
    case DegradationLevel.FULL: return true;
    case DegradationLevel.ESSENTIAL_ONLY: return ESSENTIAL_EVENTS.has(event);
    case DegradationLevel.DISABLED: return false;
  }
}
```

## Troubleshooting

### Monitoring Circuit Breaker State

```typescript
setInterval(() => {
  console.log('[CIO Circuit]', {
    state: cioBreaker.status.stats,
    isOpen: cioBreaker.opened,
    isHalfOpen: cioBreaker.halfOpen,
  });
}, 30000);
```

### Replaying Dead Letter Events

```bash
# Count dead letter entries
psql -c "SELECT count(*), event FROM cio_dead_letter GROUP BY event ORDER BY count DESC"

# Replay specific event type
node -e "
  const items = await db.query('SELECT * FROM cio_dead_letter WHERE event = $1', ['purchase']);
  for (const item of items) {
    await cio.track(item.userId, { name: item.event, data: item.data });
  }
"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
