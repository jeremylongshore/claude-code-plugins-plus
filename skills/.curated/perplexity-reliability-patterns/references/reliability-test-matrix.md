# Reliability Verification Matrix

Exercise these cases with deterministic fakes before enabling a fallback or retry policy in production. Assertions must cover observable behavior, not merely that the function returned.

| Case | Expected behavior | Forbidden behavior |
|---|---|---|
| Valid response | Return parsed answer and citations within deadline | Accept malformed required fields |
| HTTP 400/422 | Return validation failure immediately | Retry or switch models |
| HTTP 401/403 | Surface credential or authorization failure | Serve cached success or print key metadata |
| HTTP 402 | Surface billing failure | Retry another model |
| HTTP 429 | Honor bounded delay and attempt ceiling | Start parallel retries or sleep without cancellation |
| HTTP 500/503 | Count breaker failure; use compatible fallback | Replay non-idempotent work blindly |
| SDK transport/timeout class | Retry within the elapsed-time and attempt budget | Treat every statusless exception as transient |
| Unknown statusless exception | Preserve and return the original failure | Switch models or serve stale cache |
| Connect/read timeout | Abort the in-flight request | Leave a stream or socket running |
| Stream establishment stalls | Abort the request signal at the establishment deadline | Wait indefinitely before obtaining an iterator |
| Stalled stream | Abort before the next chunk deadline | Check timeout only after a late chunk arrives |
| Open circuit | Skip provider call during cool-down | Probe on every request |
| Half-open circuit | Permit one controlled probe | Release a traffic surge |
| Cache fallback | Return only same-tenant, explicitly cacheable data labeled stale | Cross tenant or retention boundary |
| Unsafe citation scheme | Reject before render | Fetch or navigate server-side |
| Local/IP citation host | Reject before render | Resolve or follow redirects |
| Bracketed or IPv4-mapped IPv6 host | Strip URL brackets, classify as IP, and reject | Allow an IP literal because `URL.hostname` retained brackets |
| Unapproved citation host | Reject or isolate | Treat model output as an allowlist decision |

## Test invariants

- Use fake clocks for retry, breaker, cache TTL, and stream-deadline tests.
- Use deterministic jitter or inject a delay function.
- Assert total attempts and elapsed budget.
- Prove a 429 waits once within budget, and prove a preferred `sonar` request is not duplicated in the fallback chain.
- Prove terminal 401 and unknown statusless errors preserve object identity and cannot read stale cache.
- Assert the abort signal reaches the active request or iterator.
- Seed cache entries for two tenants and prove isolation in both directions.
- Include `javascript:`, `data:`, userinfo, localhost, IPv4, IPv6, and deceptive subdomain citations.
- Assert logs contain no prompt, answer, raw URL, API-key fragment, or raw provider body.

## Failure classification and Retry-After helpers

Keep unknown statusless errors terminal. The statusless allowlist below is limited to documented SDK connection classes and conventional transport codes. The retry delay is clamped independently of provider input; the main workflow also enforces its elapsed-time and attempt ceilings.

```typescript
function perplexityStatus(error: unknown): number | null {
  if (typeof error !== "object" || error === null || !("status" in error)) return null;
  const status = Number((error as { status: unknown }).status);
  return Number.isInteger(status) && status >= 100 && status <= 599 ? status : null;
}

function isRetryablePerplexityError(error: unknown): boolean {
  const status = perplexityStatus(error);
  if (status !== null) return status === 408 || status === 429 || status >= 500;
  if (typeof error !== "object" || error === null) return false;

  const candidate = error as { name?: unknown; code?: unknown; cause?: unknown };
  const retryableNames = new Set(["APIConnectionError", "APIConnectionTimeoutError"]);
  const retryableCodes = new Set([
    "ECONNRESET", "ECONNREFUSED", "EHOSTUNREACH", "ENETUNREACH", "EPIPE",
    "ETIMEDOUT", "UND_ERR_CONNECT_TIMEOUT", "UND_ERR_HEADERS_TIMEOUT", "UND_ERR_SOCKET",
  ]);
  if (retryableNames.has(String(candidate.name))) return true;
  if (retryableCodes.has(String(candidate.code))) return true;
  const cause = candidate.cause;
  if (typeof cause !== "object" || cause === null) return false;
  const nested = cause as { name?: unknown; code?: unknown };
  return retryableNames.has(String(nested.name)) || retryableCodes.has(String(nested.code));
}

function boundedRetryAfterMs(error: unknown): number {
  const headers = typeof error === "object" && error !== null && "headers" in error
    ? (error as { headers: unknown }).headers
    : undefined;
  let raw: string | null = null;
  if (typeof headers === "object" && headers !== null && "get" in headers
    && typeof (headers as { get?: unknown }).get === "function") {
    raw = (headers as { get(name: string): string | null }).get("retry-after");
  } else if (typeof headers === "object" && headers !== null) {
    const record = headers as Record<string, unknown>;
    raw = String(record["retry-after"] ?? record["Retry-After"] ?? "") || null;
  }

  const seconds = raw === null ? Number.NaN : Number(raw);
  const requestedMs = Number.isFinite(seconds)
    ? seconds * 1_000
    : raw
      ? Date.parse(raw) - Date.now()
      : 250;
  return Math.min(2_000, Math.max(0, Number.isFinite(requestedMs) ? requestedMs : 250));
}
```

## Citation validator

Perform syntax and host-policy validation without backend fetching. Node's WHATWG URL implementation retains brackets in `hostname` for IPv6 literals, so strip them before `isIP` and perform the IP rejection before consulting the allowlist.

```typescript
import { isIP } from "node:net";

function validateCitations(
  citations: string[],
  allowedHosts: ReadonlySet<string>,
): Array<{ url: string; valid: boolean; reason?: string }> {
  return citations.slice(0, 20).map((raw) => {
    try {
      const url = new URL(raw);
      const serializedHost = url.hostname.toLowerCase().replace(/\.$/, "");
      const host = serializedHost.startsWith("[") && serializedHost.endsWith("]")
        ? serializedHost.slice(1, -1)
        : serializedHost;
      if (url.protocol !== "https:") return { url: raw, valid: false, reason: "https-required" };
      if (url.username || url.password) return { url: raw, valid: false, reason: "userinfo-forbidden" };
      if (host === "localhost" || isIP(host) !== 0) return { url: raw, valid: false, reason: "local-or-ip-host" };
      const allowed = [...allowedHosts].some((candidate) => {
        const normalized = candidate.toLowerCase().replace(/\.$/, "");
        return normalized !== "" && (host === normalized || host.endsWith(`.${normalized}`));
      });
      if (!allowed) return { url: raw, valid: false, reason: "host-not-allowlisted" };
      return { url: url.href, valid: true };
    } catch {
      return { url: raw, valid: false, reason: "invalid-url" };
    }
  });
}
```

## Circuit-breaker implementation

Keep the retry classifier supplied by the main skill in the same module. The breaker counts and masks only explicitly retryable failures; terminal errors escape unchanged.

```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: "closed" | "open" | "half-open" = "closed";
  private halfOpenProbe = false;

  constructor(
    private readonly threshold = 5,
    private readonly resetTimeMs = 60_000,
  ) {}

  async execute<T>(
    operation: () => Promise<T>,
    fallback: () => Promise<T>,
    isTripFailure: (error: unknown) => boolean,
  ): Promise<T> {
    if (this.state === "open") {
      if (Date.now() - this.lastFailure <= this.resetTimeMs) return fallback();
      this.state = "half-open";
    }
    if (this.state === "half-open" && this.halfOpenProbe) return fallback();
    if (this.state === "half-open") this.halfOpenProbe = true;

    try {
      const result = await operation();
      this.failures = 0;
      this.state = "closed";
      return result;
    } catch (error: unknown) {
      if (!isTripFailure(error)) throw error;
      this.failures++;
      this.lastFailure = Date.now();
      if (this.failures >= this.threshold) this.state = "open";
      return fallback();
    } finally {
      this.halfOpenProbe = false;
    }
  }

  get status() {
    return { state: this.state, failures: this.failures };
  }
}

const result = await new CircuitBreaker().execute(
  () => resilientSearch(query, "sonar-pro"),
  () => getCachedResult(query),
  isRetryablePerplexityError,
);
```

## Rollout evidence

Record baseline and canary error rate, p50/p95/p99 latency, retry amplification, fallback rate, circuit state transitions, cache age, and user-visible degradation. Establish rollback thresholds before rollout; do not invent them during an incident.

## Primary references

- [Perplexity SDK error handling](https://docs.perplexity.ai/docs/sdk/error-handling)
- [Perplexity SDK configuration](https://docs.perplexity.ai/docs/sdk/configuration)
- [Sonar response structure](https://docs.perplexity.ai/docs/sonar/openai-compatibility)
