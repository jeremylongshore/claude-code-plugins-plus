---
title: "SSE on Cloud Run: Every Platform Lie You Hit in Production"
description: "SSE looks simple until you deploy it. Firebase Hosting buffers streams. Cloud Run kills your CPU. Fastify CORS skips raw writes. Nine PRs to learn the hard way."
date: "2026-03-04"
tags: ["debugging", "devops", "full-stack", "typescript", "architecture", "cloud"]
featured: false
---
Server-Sent Events are the simplest real-time protocol on the web. One HTTP connection. Text frames. No WebSocket handshake. Every tutorial makes it look trivial.

Then you deploy to Cloud Run behind Firebase Hosting and spend nine PRs discovering that every platform between your code and the browser has opinions about HTTP responses — and SSE violates most of them.

This is the story of building real-time game updates for a Braves broadcast dashboard. Each fix revealed the next layer of broken assumptions.

## The Setup

The Braves Booth Intelligence dashboard needs live data during games. A backend poller checks the GUMBO feed (MLB's live game API) every few seconds and pushes updates to connected browsers via SSE. Simple architecture:

```
GUMBO Feed → Poller → SSE Handler → Browser EventSource
```

Locally, this works perfectly. Docker Compose, Fastify backend, React frontend. SSE connections stay open, events flow, data renders. Ship it.

## Layer 1: The Dockerfile Lies (PR #8-9)

First deploy to Cloud Run. Service won't start. The Dockerfile had `COPY team-config.json` referencing a path that existed in dev but not in the build context. Classic — your Dockerfile works with `docker compose` because the build context is the repo root, but Cloud Run builds from a different context.

Fixed the COPY path. Service starts. Frontend can't reach the backend. Why? The Vite dev proxy was configured to hit `localhost:3001`, but in Docker the backend service has a DNS name. Changed the proxy target to the Docker service name. Two PRs for two problems that don't exist on your laptop.

## Layer 2: Cloud Run Kills Your CPU (PR #11)

Dashboard deploys. SSE connections establish. Data flows for about 30 seconds, then stops. The connection stays open but no events arrive.

Cloud Run's default behavior: **CPU is only allocated during request processing.** Between HTTP requests, your container gets zero CPU. An SSE connection is a single long-lived request — Cloud Run sees it as idle and throttles the CPU to zero. Your `setInterval` poller stops running. Your event loop freezes. The connection looks alive but nothing happens.

The fix is a configuration flag:

```yaml
# Cloud Run service config
cpu-throttling: false
min-instances: 1
```

`cpu-throttling: false` means "always allocate CPU, even between requests." `min-instances: 1` means "don't scale to zero." You're paying for an always-on instance now. SSE isn't serverless-friendly, and pretending otherwise wastes days.

## Layer 3: Cloud Run Kills Your Process (PR #12)

CPU throttling fixed. Events flow again. Then they stop after a few minutes of no browser connections. Reconnect — no data. Check logs — the poller isn't running.

The poller was running in-process with the Fastify server. It starts on boot, checks GUMBO every 10 seconds, stores latest data in memory. But Cloud Run kills instances that receive no HTTP traffic, even with `min-instances: 1`. No connected SSE clients = no active requests = instance eligible for shutdown.

When a new browser connects, Cloud Run spins up a fresh instance. The poller starts, but there's a gap — no cached data, and the first poll hasn't completed yet.

The architectural fix: **move the poller inside the SSE handler.** When a client connects, the handler starts polling. When the last client disconnects, polling stops. The poller lifecycle is tied to active connections, not to process boot. This aligns with Cloud Run's model instead of fighting it.

```typescript
// Poller runs only when clients are connected
let activeClients = 0;
let pollerInterval: NodeJS.Timeout | null = null;

function startPollerIfNeeded() {
  if (pollerInterval) return;
  pollerInterval = setInterval(pollGumbo, 10_000);
  pollGumbo(); // immediate first poll
}

function stopPollerIfIdle() {
  if (activeClients === 0 && pollerInterval) {
    clearInterval(pollerInterval);
    pollerInterval = null;
  }
}
```

## Layer 4: Firebase Hosting Buffers Your Stream (PR #13)

Poller restructured. Locally everything works. Deploy. SSE connections establish but events arrive in bursts — 10-15 events dumped at once after long silences.

Firebase Hosting acts as a reverse proxy in front of Cloud Run. Reverse proxies buffer responses. They collect chunks and forward them in batches for efficiency. This is correct behavior for normal HTTP responses. For SSE, it's fatal. The whole point of SSE is that each event arrives immediately when sent.

Firebase Hosting has no `X-Accel-Buffering: no` support. No configuration to disable response buffering for specific routes. It simply buffers, and there's no workaround.

The fix: **bypass Firebase Hosting entirely for SSE.** The frontend connects directly to the Cloud Run service URL for the event stream:

```typescript
// Don't go through Firebase Hosting for SSE
const SSE_URL = import.meta.env.VITE_CLOUD_RUN_URL;

const eventSource = new EventSource(`${SSE_URL}/api/sse/game`);
```

Firebase Hosting still serves the static frontend assets. Only the SSE connection goes direct to Cloud Run. Two origins now, which means CORS.

## Layer 5: Fastify CORS Doesn't Apply to Raw Writes (PR #14)

Direct Cloud Run SSE connection. Browser immediately rejects it: `No 'Access-Control-Allow-Origin' header is present on the requested resource.`

But Fastify's CORS plugin is registered. It works for every other endpoint. Why not SSE?

Because SSE handlers use raw Node.js response writes. Fastify's CORS plugin operates on Fastify's response abstraction — it hooks into `onSend` to add headers. When you call `res.raw.writeHead()` to set up the SSE stream, you're bypassing Fastify entirely. The CORS headers never get added.

```typescript
server.get('/api/sse/game', (request, reply) => {
  const raw = reply.raw;

  // Fastify CORS plugin will NEVER touch these headers
  // because we're writing directly to the Node.js response
  raw.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Access-Control-Allow-Origin': process.env.CORS_ORIGIN || '*',
  });

  raw.write(`data: ${JSON.stringify({ type: 'connected' })}\n\n`);

  const onData = (event: string) => raw.write(`data: ${event}\n\n`);
  emitter.on('game-update', onData);

  request.raw.on('close', () => {
    emitter.off('game-update', onData);
    activeClients--;
    stopPollerIfIdle();
  });

  activeClients++;
  startPollerIfNeeded();
});
```

The `Access-Control-Allow-Origin` header must be set manually in the `writeHead` call. This isn't documented in Fastify's CORS plugin because it's not a Fastify problem — it's a consequence of dropping to raw Node.js responses.

## The Scorecard

Nine PRs (8 through 15, plus the feature PR). Five distinct platform behaviors that don't surface until production:

| PR | Problem | Root Cause |
|----|---------|------------|
| #8-9 | Service won't start | Docker build context differs from compose |
| #11 | Events stop after 30s | Cloud Run CPU throttling |
| #12 | Poller dies between connections | Cloud Run instance lifecycle |
| #13 | Events arrive in bursts | Firebase Hosting response buffering |
| #14 | CORS rejection | Raw writeHead bypasses Fastify plugins |

Each fix took 15-60 minutes. Finding each problem took longer. The pattern: fix one layer, the next layer's assumptions become visible.

## Meanwhile: WebGL DXF Viewer (cad-dxf-agent)

While the SSE saga played out, the CAD DXF agent got a major upgrade: interactive WebGL rendering of 2D engineering drawings. Previously, the viewer rendered static PNGs. Now it's full pan/zoom/inspect with a side-by-side comparison view.

The comparison tab lets you overlay original and edited DXF files to see exactly what changed — critical for engineering review where a misplaced line segment matters. Eleven end-to-end tests cover the interactive viewer, including fetch timeouts and friendly error states.

This is also where global E2E setup got properly wired — auth token handling and a sidebar-close fix that was causing flaky tests across the suite.

## The Lesson

SSE is not WebSockets. It's simpler. But "simpler" means every HTTP intermediary thinks it understands your response — and handles it wrong.

If you're deploying SSE to any managed platform:

1. **Check CPU allocation.** Serverless platforms throttle idle connections.
2. **Check response buffering.** Every reverse proxy between you and the browser will buffer by default.
3. **Check your framework's CORS.** If you're writing raw responses, framework middleware doesn't apply.
4. **Tie your background work to active connections.** Don't assume your process stays alive.

The protocol is 10 lines of code. The production deployment is nine PRs and five hard-won lessons about what "managed" actually means.

---

## Related Posts

- [Zero to CI: Full-Stack Dashboard in One Session](/posts/zero-to-ci-full-stack-dashboard-one-session/) — The initial build of this same Braves dashboard
- [The Silent Killer: How Bare catch {} Blocks Hide Failures](/posts/silent-killer-bare-catch-blocks-hide-failures/) — Another debugging saga where the platform hid the real error
- [Session Cookies, Forgot-Password Timeouts, and Flaky E2E Tests](/posts/session-cookies-forgot-password-flaky-e2e-tests/) — Firebase Hosting strikes again with timeout surprises
