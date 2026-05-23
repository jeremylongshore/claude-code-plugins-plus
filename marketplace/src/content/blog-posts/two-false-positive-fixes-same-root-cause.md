---
title: "Two False-Positive Fixes, Same Root Cause"
description: "Two separate false-positive alerts, same root cause: monitoring conjoined liveness with conditional behavior. Separating health signals quiets noise under load."
date: "2026-05-11"
tags: ["docker", "healthchecks", "monitoring", "ci-cd", "observability", "production-engineering"]
featured: false
---
Two separate monitoring failures on the same day, same root cause. Both fixed by answering a single question: "Am I testing for health, or am I testing for perfect conditions?" The distinction matters because perfect conditions are temporary, and health is structural. And once you see the pattern once, you see it everywhere.

## Context: production on a shared VPS

The Braves stack runs on Contabo (24 GiB RAM, 6 CPUs). Five Docker stacks share that hardware: Braves (frontend, backend, pybaseball), Plane (13 containers), Twenty (5 containers), Umami (3 containers), and ntfy (1 container). 25 containers total. Single ingress: Caddy reverse proxy. Single disk. When one stack's load spikes, all five feel it.

This architecture means healthchecks and deployment validators are sensitive to global state, not just stack-local state. A healthcheck that works under isolated test conditions can fail when the VPS is under collective load. A validator that passes in the afternoon can fail at 2 AM when a different stack is doing batch work.

## The symptom

On May 11, two separate failure modes emerged:

1. **False-positive container-unhealthy alerts firing ~10 times per day.** Each one triggered: manual inspection, "nope, it's fine," return to normal operations. Repeat. The notification log became noise.
2. **Every off-hours deploy auto-rolling back without an obvious cause.** Off-season deployments (which are mostly off-hours) all failed smoke checks and rolled back. The CI pipeline was effectively blocked for non-emergency pushes.

Both failures traced to monitoring expressions that mixed structural health signals with situational condition signals.

## Fix one: TCP over HTTP fetch

### The setup

Healthchecks for the Braves containers ran every 10 seconds, invoking Node's global `fetch` (or `urllib.request` for the Python service) to make an HTTP round-trip to a local status endpoint. The logic was straightforward: open connection, validate response, exit on failure. The Docker healthcheck timeout was 5 seconds.

Performance profile:

- Light load (loadavg < 2): fetch completed in 5–20 ms.
- Moderate load (loadavg 2–8): fetch completed in 100–500 ms.
- High load (loadavg > 10): fetch sometimes failed to complete within 5 seconds.

### The failure cascade

When the healthcheck timed out:

1. Docker retried the check every 10 seconds.
2. After 5 consecutive timeouts (50 seconds), Docker marked the container unhealthy.
3. Netdata observed the state change and fired a `docker_container_unhealthy` alert.
4. The alert flowed through ntfy to mobile notifications: "scorecardecho is down."
5. Manual inspection: the container was fine, the process was responding, load was just high.
6. Clear the alert, wait for the cycle to repeat.

This happened ~10 times per day, every single day.

### The assumption that bit

Fetch-based healthchecks assume light load. They assume:

- The event loop has microseconds to spare for I/O
- The network isn't congested
- The kernel isn't swapping
- No other workload is competing for scheduler time

All true most of the time. Not true on a shared VPS where 24 other production containers are running. Not true when pybaseball is churning through XML parsing. Not true when Plane is sync-checking its database. The healthcheck assumed the happy path—and the production VPS spends most of its time off the happy path.

### The fix (commit `cbb4f6e`)

Replace the HTTP fetch with a raw TCP connect. Verification moves from the application layer down to a single SYN/ACK exchange — the work the kernel was already doing to accept the connection.

```diff
  healthcheck:
-   test: ["CMD-SHELL", "node -e \"fetch('http://localhost:3001/api/health').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))\""]
-   interval: 10s
+   test: ["CMD-SHELL", "node -e \"require('net').connect(3001,'localhost').on('connect',function(){this.end();process.exit(0)}).on('error',function(){process.exit(1)})\""]
+   interval: 30s
    timeout: 5s
-   retries: 5
+   retries: 3
+   start_period: 15s
```

The Python service got the equivalent treatment:

```diff
- test: ["CMD-SHELL", "python3 -c \"import urllib.request; urllib.request.urlopen('http://localhost:8001/health')\" || exit 1"]
+ test: ["CMD-SHELL", "python3 -c \"import socket; s=socket.create_connection(('localhost',8001),2); s.close()\""]
```

Both new checks open a TCP connection to the port, immediately close it, and exit. No HTTP parsing. No JSON. No event-loop work beyond the socket call itself. The kernel completes the SYN/ACK in microseconds even when the application thread is stalled. This pattern works in any container image that already has `node` or `python3` — no extra binaries to install.

### Tuning alongside the fix

Three other changes shipped together:

- **Interval 10s → 30s:** Polling three times less frequently means 3× fewer state transitions, 3× fewer container-state callback executions, 3× fewer potential false positives.
- **Retries 5 → 3:** Before: unhealthy after 50 seconds. After: unhealthy after 90 seconds. Trades slightly earlier detection of real outages for dramatically lower false-positive noise.
- **`start_period: 15s` added:** Containers no longer fail healthcheck during startup when they're still bootstrapping.

### Operational pairing: Netdata hold-down

The VPS runs Netdata for monitoring. A separate change added a 2-minute hold-down before alerting on `docker_container_unhealthy`. A brief glitch—a 10-second spike in load, a temporary network hiccup—can't page anymore. It has to persist for 120 seconds.

### Result

Unhealthy alerts dropped from ~10 per day to zero. The notification log went silent.

## Fix two: drop the mode signal from deployment validation

### The setup

The deployment smoke check for the Braves backend used a jq filter applied to the app's status endpoint:

```jq
.status == "ok" and .gumbo.running == true
```

The first part is a liveness signal: the app is responding and healthy. The second part is a mode signal: the gumbo processor (which handles game-update XML) is currently running. When this filter was written—probably during baseball season when games are daily—both conditions made intuitive sense. Both seemed permanent.

### The failure cascade

Most of the calendar is *between* games:

- Off-season (November–March)
- Post-game (after each game ends)
- Pre-game (before first pitch, morning hours)

During these windows, `gumbo.running` is false. Most deployments happen off-hours. So most off-hours deployments triggered a smoke check that required `gumbo.running == true`. The app was fine. The status was `"ok"`. But the game processor was inactive. The filter conjunction failed. The deployment workflow interpreted the failure as "deployment is broken, roll back." Automatic rollback fired. Every single off-hours deploy. Without exception.

This blocked the entire CI pipeline for off-season work. No off-hours deployments could land unless manually overridden.

### The assumption that bit

`gumbo.running` is a *temporary* signal. It's true when a game is in progress. False when there isn't one. During the offseason it's false for months straight.

The smoke check mixed a permanent structural signal (`status == "ok"` = the app is healthy) with a temporary situational signal (`gumbo.running == true` = a game is active right now). It required both to be true, as if they were equivalent. They aren't. An app is healthy between games just as much as it's healthy during games. Health and game-processing mode are orthogonal.

### The fix (commit `5b9fe26`)

Remove the mode condition entirely. The filter now simply validates health:

```diff
-.status == "ok" and .gumbo.running == true
+.status == "ok"
```

A single question: "Is the app responding correctly?" Nothing about what it's processing. Nothing about external conditions.

### Result

Off-hours deployments stopped auto-rolling back. The CI pipeline unblocked. Every deploy now passes smoke validation as long as the app is actually healthy, regardless of whether a game is in progress.

## The shared lesson

Both fixes follow the same pattern: a monitoring expression conjoined two signals where one was structural and the other was situational.

| Fix | Structural Signal | Situational Signal | Status |
|-----|-------------------|-------------------|--------|
| #1 (healthcheck) | "Process is listening on port 3000" | "Load is light enough for a 5-second fetch" | Always true? No. |
| #2 (smoke check) | "App responds with ok status" | "Game processor is running" | Always true? No. |

When the situational signal became false—as situational signals do—the conjunction failed, and the alarm fired. The system was healthy. The alarm was noise.

The pattern emerges because it *feels* right when you write it. "The app should be healthy *and* the load should be light." "The container should be healthy *and* the game should be in progress." Both conditions seem like they should always be true. They're not. Situational conditions change. The moment you conjoin them with structural health signals, you've created a trap. The conjunction becomes true only under the narrow circumstances you happened to be testing in.

### Three ways to break the trap

#### Remove the situational condition

Ask only the health question. Strip the conjunction down to the structural signal.

#### Move to a separate alert

"Is the app healthy?" and "Is the game processor running?" are two questions. They should be two checks, not one. Alert on each independently.

#### Document the assumption

If the check fails when a situational condition flips, say so in the alert message so responders know the system is fine without manual intervention.

### The checklist before merging a monitoring expression

List every condition it depends on staying true:

- "This healthcheck assumes load is under threshold N."
- "This smoke check assumes a game is in progress."
- "This alert assumes the cache is populated."
- "This validator assumes the external service is available."

If any condition can become false — and most can — apply one of the three fixes above.

A healthcheck should answer: "Is this process alive?" A deployment validator should answer: "Does the app respond correctly?" Neither should answer: "And is everything perfect?" Perfect is temporary. Healthy is structural.

---

**Also shipped:** hubspot-pack v2.0.0 landed the same day, consolidating 30 templated skills into 10 production-engineering skills following the guidewire v2 pattern. Also: porkbun-dnssec-caa.sh script pinning DNSSEC/CAA on intentsolutions.io as a Rekor predicate precondition.
