# Errors — podium-rate-limit-survival

Lookup table for `ERR_RL_*` codes raised by the library and operator scripts. Each entry: cause, detection point, and the action to take.

## ERR_RL_001 — rate_limited_per_minute

- **HTTP**: 429 from any `api.podium.com/v4/*` endpoint
- **Cause**: Per-minute envelope (documented 60 req/min) exceeded. The bucket should make this unreachable; if it fires, either the bucket is misconfigured (capacity too high, rate too high) or external clients are sharing the OAuth app's quota.
- **Detection**: `podium_call_with_retry()` observes a 429 response.
- **Action**: Parse `Retry-After`, sleep (capped at 120s), retry up to `max_attempts`. If 429 persists after all attempts, raise `PodiumRateLimitError`. Audit the bucket configuration: `sum(per_endpoint[*].rate_per_minute) <= bucket.rate_per_minute` must hold.

## ERR_RL_002 — rate_limited_daily_envelope

- **HTTP**: 429 or 400 with body `{"error": "quota_exhausted"}` (Podium returns either depending on endpoint)
- **Cause**: 24-hour envelope hit. Daily quota counter should have fired the throttle alert at 95% before this; if it fires without prior alert, the counter store (Redis/SQLite) is desynchronized from actual call count.
- **Detection**: 429 with `Retry-After` > 3600 seconds, or 400 with `quota_exhausted` body.
- **Action**: Hard-stop the offending endpoint family until UTC midnight. Verify the daily counter is incrementing — Redis `GET podium:quota:YYYY-MM-DD` should be near 50,000. If the counter is far below quota but Podium is rejecting, the counter store has lost increments and operators must investigate Redis evictions, SQLite corruption, or sharding bugs.

## ERR_RL_003 — retry_after_malformed

- **HTTP**: N/A (raised by `parse_retry_after`)
- **Cause**: 429 response carried a `Retry-After` header in neither integer-seconds nor RFC 7231 HTTP-date form.
- **Detection**: Both parsers in `parse_retry_after()` failed; the function falls back to the default (60s) and logs a warning.
- **Action**: No automated recovery needed — the fallback is safe. Log the raw header value for analysis; if Podium changed the header format, update `parse_retry_after()` to handle the new shape.

## ERR_RL_004 — daily_quota_warn

- **HTTP**: N/A (logged by `DailyQuotaMonitor`)
- **Cause**: Daily quota consumption crossed the 70% warn threshold.
- **Detection**: `check_and_alert()` returns `"warn"`.
- **Action**: No immediate action. Log to the ops-warning channel. If warn fires before noon UTC, project forward: 70% by noon = 100%+ by midnight. Consider preemptive throttle.

## ERR_RL_005 — daily_quota_page

- **HTTP**: N/A (paged by `DailyQuotaMonitor`)
- **Cause**: Daily quota consumption crossed the 85% page threshold.
- **Detection**: `check_and_alert()` returns `"page"`.
- **Action**: Page on-call. Operator identifies which endpoint family is leading consumption (per-family structured logs), considers reducing that family's bucket rate by 25%, and confirms throttle behavior fires correctly at 95% as a safety net.

## ERR_RL_006 — daily_quota_throttle_engaged

- **HTTP**: N/A (raised by `DailyQuotaMonitor` and the bucket layer)
- **Cause**: Daily quota consumption crossed the 95% throttle threshold; bucket rate is reduced by `throttle_rate_multiplier` (default 50%) until UTC midnight.
- **Detection**: `check_and_alert()` returns `"throttle"`; bucket reads the throttle flag and adjusts `rate_per_sec`.
- **Action**: Page on-call. Verify the throttle is in effect (`bucket.rate_per_sec` halved). Low-priority outbound work degrades; foreground work (webchat replies, etc.) continues. If foreground work also degrades, raise the throttle multiplier toward 1.0 temporarily and accept the quota-breach risk.

## ERR_RL_007 — burst_smoother_queue_overflow

- **HTTP**: N/A (raised by `BurstSmoother`)
- **Cause**: A batch submitted to `BurstSmoother.submit_batch()` exceeded `max_batch_size` (default 200).
- **Detection**: `submit_batch()` raises before draining.
- **Action**: Spill the excess to a durable queue (caller-provided). Smoother is designed for end-of-day clusters of dozens to low hundreds; batches in the thousands belong on a queue.

## ERR_RL_008 — admission_denied

- **HTTP**: N/A (returned as `False` by `AdmissionController.admit()`)
- **Cause**: Projected outbound cost for an inbound event exceeded 5% of remaining daily budget.
- **Detection**: `admit()` returns `False`; structured log records the event type, cost, and remaining budget.
- **Action**: Caller returns non-2xx to the webhook source (Podium retries automatically) OR queues the event to a durable store for replay when the daily quota recovers. Sustained denials over 5+ minutes indicate amplification factors are mistuned — measure actual outbound-per-inbound ratio and update the factor map.

## ERR_RL_009 — per_endpoint_allocation_invalid

- **HTTP**: N/A (raised at startup by config loader)
- **Cause**: Sum of `per_endpoint[*].rate_per_minute` exceeds `bucket.rate_per_minute`. The isolation guarantee is forfeit.
- **Detection**: Config loader validates the invariant and raises on mismatch.
- **Action**: Reduce per-family allocations until the sum matches the global ceiling. The default allocation in `config/settings.yaml` is correct; any divergence is operator-applied.

## ERR_RL_010 — redis_unavailable_fallback_to_sqlite

- **HTTP**: N/A (logged by `DailyQuotaMonitor`)
- **Cause**: Redis connection failed; daily-quota counter switched to local SQLite.
- **Detection**: `redis.asyncio` raises; the monitor catches and reroutes to SQLite.
- **Action**: No immediate action — the integration continues. Investigate Redis health. SQLite is single-process; if multiple processes are running, the daily counter will under-count and quota breaches may go undetected. Restore Redis before the next burst window.

## ERR_RL_011 — bucket_acquire_timeout

- **HTTP**: N/A (raised by foreground task with a timeout on `bucket.acquire()`)
- **Cause**: A request waited longer than the caller's timeout for a bucket slot. Indicates sustained over-allocation, not a bucket bug.
- **Detection**: Caller's `asyncio.wait_for(bucket.acquire(), timeout=N)` raises `TimeoutError`.
- **Action**: Caller decides — drop the request, queue for replay, or return a soft-fail to its own caller. Audit the foreground rate against the bucket rate; if foreground is sustained > bucket rate, the integration is over-subscribed and needs a bucket-rate increase (with quota implications) or a foreground-rate decrease.

## ERR_RL_012 — retry_after_exceeds_cap

- **HTTP**: N/A (logged by `podium_call_with_retry`)
- **Cause**: Server returned a `Retry-After` greater than `retry_after_cap_seconds` (default 120s).
- **Detection**: Parsed wait > cap.
- **Action**: Cap and proceed. If Podium consistently returns very long Retry-After values, that's a signal the daily envelope is hit — `ERR_RL_002` applies and the cap is masking it. Inspect the response body for `quota_exhausted`.

## ERR_RL_013 — cross_family_contagion_suspected

- **HTTP**: N/A (correlation log)
- **Cause**: One endpoint family's 429 rate spiked, and a *different* family's 429 rate spiked within the same minute. Suggests the global ceiling is firing across families, which the per-family bucket isolation is meant to prevent.
- **Detection**: Operator dashboard or log correlation query.
- **Action**: Re-validate `sum(per_endpoint[*].rate_per_minute) == bucket.rate_per_minute`. If the sum is correct but contagion persists, the OAuth app's per-minute ceiling is lower than 60 — measure with a controlled burst against a single family and recalibrate.

## ERR_RL_014 — amplification_factor_drift

- **HTTP**: N/A (capacity-planning observation)
- **Cause**: Measured outbound-per-inbound ratio diverged from the configured `amplification.factors` value. Admission control now denies too few (over-admitting) or too many (under-admitting) events.
- **Detection**: Capacity-planning report comparing event log (inbound) against bucket log (outbound).
- **Action**: Update `config/settings.yaml` `amplification.factors` to match measured ratios. If a new event type appears in inbound traffic that isn't in the map, it defaults to factor 1 and may be admitting too easily — add an explicit entry.
