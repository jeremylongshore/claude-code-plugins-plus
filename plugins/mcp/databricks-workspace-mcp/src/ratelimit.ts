/**
 * Token-bucket rate limiter, applied per endpoint family so a burst of cluster-events calls
 * can't starve a pipelines call (and vice-versa). Databricks rate limits are per-endpoint, so
 * one bucket per family mirrors the server's own accounting.
 *
 * Clock and sleep are injectable so tests run instantly and deterministically.
 */

export interface RateLimiterOptions {
  /** Max tokens in the bucket (burst size). */
  capacity: number;
  /** Tokens refilled per second. */
  refillPerSec: number;
  now?: () => number;
  sleep?: (ms: number) => Promise<void>;
}

export class RateLimiter {
  private tokens: number;
  private readonly capacity: number;
  private readonly refillPerSec: number;
  private last: number;
  private readonly now: () => number;
  private readonly sleep: (ms: number) => Promise<void>;

  constructor(opts: RateLimiterOptions) {
    this.capacity = opts.capacity;
    this.refillPerSec = opts.refillPerSec;
    this.tokens = opts.capacity;
    this.now = opts.now ?? Date.now;
    this.sleep = opts.sleep ?? ((ms) => new Promise((r) => setTimeout(r, ms)));
    this.last = this.now();
  }

  private refill(): void {
    const t = this.now();
    const elapsedSec = (t - this.last) / 1000;
    if (elapsedSec > 0) {
      this.tokens = Math.min(this.capacity, this.tokens + elapsedSec * this.refillPerSec);
      this.last = t;
    }
  }

  /** Block until a token is available, then consume it. */
  async acquire(): Promise<void> {
    // Loop guards against the wake-up racing another acquirer.
    // eslint-disable-next-line no-constant-condition
    while (true) {
      this.refill();
      if (this.tokens >= 1) {
        this.tokens -= 1;
        return;
      }
      const deficit = 1 - this.tokens;
      const waitMs = Math.ceil((deficit / this.refillPerSec) * 1000);
      await this.sleep(waitMs);
    }
  }
}

/** Registry of per-family limiters with sensible Databricks-friendly defaults. */
export class FamilyRateLimiters {
  private readonly limiters = new Map<string, RateLimiter>();
  constructor(
    private readonly factory: (family: string) => RateLimiter = () =>
      new RateLimiter({ capacity: 10, refillPerSec: 5 }),
  ) {}

  async acquire(family: string): Promise<void> {
    let l = this.limiters.get(family);
    if (!l) {
      l = this.factory(family);
      this.limiters.set(family, l);
    }
    await l.acquire();
  }
}
