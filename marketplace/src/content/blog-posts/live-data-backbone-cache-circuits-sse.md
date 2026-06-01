---
title: "Live Data Backbone: Cache Layers, Circuit Breakers, and SSE for Broadcast"
description: "Wiring MLB Stats API, GUMBO feeds, and Statcast into a fault-tolerant data layer with TTL caching, circuit breakers, and Server-Sent Events."
date: "2026-03-02"
tags: ["full-stack", "architecture", "typescript", "fastapi", "python", "devops"]
featured: false
---
Yesterday was the scaffold. Today the data actually flows.

The Braves Booth Intelligence dashboard is worthless without live data. And live data during a broadcast has exactly one rule: **never show an error screen**. No spinners. No 500s. No "service unavailable." The broadcast doesn't pause while your API recovers.

That constraint shaped every design decision today. Ten commits, two merged PRs, and one architecture principle: every data source gets a cache layer, a circuit breaker, and a graceful degradation path.

## The Data Sources

Four feeds power the dashboard:

| Source | What It Provides | Update Frequency |
|--------|-----------------|-----------------|
| MLB Stats API | Rosters, schedules, standings, player stats | Pre-game + between innings |
| GUMBO Feed | Live game state — pitch-by-pitch, runners, score | Every pitch (~20s) |
| Statcast (pybaseball) | Exit velocity, launch angle, sprint speed, park factors | Pre-game batch + on-demand |
| Weather + Umpire | Wind, temperature, ump strike zone tendencies | Pre-game only |

Each one fails differently. MLB Stats API rate-limits you. GUMBO feeds lag during high-traffic games. Pybaseball downloads sometimes timeout. Weather APIs go down during storms — exactly when you need them most.

## HTTP Client + TTL Cache

Every external call goes through a centralized HTTP client with an in-memory TTL cache. The critical pattern:

```python
async def get(self, url: str, ttl: int | None = None) -> dict:
    entry = self._cache.get(url)
    if entry and not entry.expired:
        return entry.data
    try:
        resp = await self._session.get(url)
        resp.raise_for_status()
        self._cache[url] = CacheEntry(data=resp.json(), ttl=ttl)
        return resp.json()
    except httpx.HTTPError:
        if entry:  # Stale data beats no data
            return entry.data
        raise
```

When a fresh fetch fails, stale data is returned instead of an error. During a broadcast, showing a stat from 30 seconds ago is infinitely better than showing nothing. TTLs vary: roster data caches for an hour, GUMBO game state for 15 seconds, weather for 30 minutes.

## Circuit Breaker Pattern

The cache handles transient failures. Circuit breakers handle sustained outages. When an external API fails repeatedly, stop calling it. Don't pile up timeouts.

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.state = CircuitState.CLOSED
        self.failure_count = 0

    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitOpenError(self.recovery_timeout)
        try:
            result = await func(*args, **kwargs)
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            return result
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
            raise
```

Three states. CLOSED means healthy — calls pass through. After five consecutive failures, the circuit OPENS and calls are rejected immediately. After 60 seconds, HALF_OPEN lets one test call through. The Statcast endpoint wraps pybaseball with this pattern because pybaseball downloads large CSV files from Baseball Savant, and those downloads fail unpredictably.

## GUMBO Feed Polling

MLB's GUMBO feed is the heartbeat of live game data. JSON endpoint, updates every pitch with the full game state. The poller runs on a background task with adaptive intervals — 5 seconds between pitches, 30 seconds during commercial breaks.

The key design choice: the poller tracks `_last_play_id` and only publishes to the event bus when the at-bat index changes. No duplicate events. The frontend doesn't re-render unless there's new data to show.

## SSE Event Bus

Server-Sent Events push data to the frontend. Not WebSockets. SSE is simpler, auto-reconnects, and the data flow is one-directional — exactly what a dashboard needs.

```python
class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}

    async def publish(self, channel: str, data: dict):
        for queue in self._subscribers.get(channel, []):
            await queue.put(data)

    async def subscribe(self, channel: str) -> AsyncGenerator:
        queue = asyncio.Queue()
        self._subscribers.setdefault(channel, []).append(queue)
        try:
            while True:
                data = await queue.get()
                yield f"event: {channel}\ndata: {json.dumps(data)}\n\n"
        finally:
            self._subscribers[channel].remove(queue)
```

The event bus is the glue. GUMBO poller publishes game state. Statcast publishes pitch metrics. The frontend opens one SSE connection per channel and renders updates as they arrive.

## Pre-Game Prefetcher + Graceful Degradation

Caches are useless when cold. The prefetcher warms them: `make prefetch GAME=748231`. It fetches rosters, player stats, matchup history, park factors, weather, and umpire tendencies — all in parallel, all cached with appropriate TTLs. Run it 30 minutes before first pitch. By the time the mic goes hot, every API call hits cache.

Every endpoint follows a degradation contract. The matchup history endpoint tries three sources in order: local cache, MLB Stats API, then Statcast aggregation. If all three fail, it returns `{"available": false, "reason": "data_unavailable"}`. The frontend renders a dash instead of a number. No crash. No error modal. The frontend never handles HTTP errors — it only handles data presence.

## Side Quest: cad-dxf-agent v0.4.0

Between data layer commits, I shipped [cad-dxf-agent v0.4.0](https://github.com/jeremylongshore/cad-dxf-agent/releases/tag/v0.4.0). Test coverage went from 89% to 95% across all modules. Docker ODA install is now optional with a file-size guard so the image doesn't bloat when ODA isn't needed. Added a web app quick reference card for end users.

Small release. Clean release. The kind you ship between innings.

## What's Next

The data layer is done. Every source has caching, circuit breaking, and degradation paths. Tomorrow: wiring these feeds into the frontend panels so the dashboard actually shows live numbers. Then testing under simulated game load — because the real test is whether it holds up when 300 pitches flow through in three hours.

First pitch is coming. The data backbone is ready.

---

### Related Posts

- [Zero to CI: Full-Stack Dashboard in One Session](/blog/zero-to-ci-full-stack-dashboard-one-session/) — Day one scaffold for this project
- [Building a Deterministic DXF Comparison Engine in One Day](/blog/deterministic-dxf-comparison-engine-one-day-build/) — Same build-fast methodology, different domain
- [Production Release Engineering v4.5.0](/blog/production-release-engineering-v450/) — Release discipline applied to the CAD agent
