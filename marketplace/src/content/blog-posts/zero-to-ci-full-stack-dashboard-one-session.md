---
title: "Zero to CI: Full-Stack Dashboard in One Session"
description: "11 commits from empty repo to green CI. Building the Braves Booth Intelligence dashboard with opinionated stack choices and a CAD agent side quest."
date: "2026-03-01"
tags: ["full-stack", "react", "typescript", "fastapi", "docker", "ci-cd", "architecture"]
featured: false
---
Empty directory at 8 AM. Green CI pipeline by dinner. 30 commits across two projects. Here's how the day went.

## The Project: Braves Booth Intelligence

The Atlanta Braves radio broadcast team needs real-time data during games. Statcast metrics, park factors, cohost context, narrative threads — all on a dark dashboard optimized for a broadcast booth where you glance, grab a number, and keep talking.

This isn't a web app that happens to show baseball data. It's a broadcast operations tool. That distinction drives every technical decision.

## The Stack (and Why Each Piece)

| Layer | Choice | Why Not the Alternative |
|-------|--------|------------------------|
| Frontend | React 18 + Vite 6 + TypeScript 5.7 | Next.js is overkill — no SSR needed for a booth dashboard |
| CSS | Tailwind v4 | CSS-first config, no `tailwind.config.js` |
| Backend | Fastify 5 + pino | Express is slow and has no built-in schema validation |
| Database | SQLite + better-sqlite3 | No network round trips. WAL mode. Broadcast can't wait for Postgres |
| Data | FastAPI + pybaseball | Statcast is Python-native. Don't fight it |
| Infra | Docker Compose | Three services, health checks, one command |
| CI | GitHub Actions | 4 parallel jobs, nothing fancy |

The most controversial choice is SQLite for a "real" application. But think about it: the broadcast booth is a single-user environment. The data is small — one team's season stats, narrative logs, cohost preferences. WAL mode gives you concurrent reads during writes. And when your database is a file on disk, your latency floor is zero network hops.

## Commit 1: Specification First

Before writing a line of application code, I wrote 12 specification documents. Firebase hosting config. Project journal. Architecture decisions.

This isn't ceremony. It's insurance. When you're building fast, specs keep you from solving the wrong problem at full speed.

## Commits 2-5: Frontend in Four Steps

### Tailwind v4's CSS-First Config

Tailwind v4 killed the JavaScript config file. Design tokens live in CSS where they belong:

```css
@import "tailwindcss";

@theme {
  --color-braves-navy: #13274F;
  --color-braves-red: #CE1141;
  --color-braves-gold: #EAAA00;
  --color-braves-white: #FFFFFF;

  --color-surface-primary: #0F1419;
  --color-surface-secondary: #1A1F2E;
  --color-surface-tertiary: #242B3D;

  --font-display: "Bebas Neue", sans-serif;
  --font-body: "DM Sans", sans-serif;
  --font-data: "DM Mono", monospace;
}
```

Three font families: Bebas Neue for big display numbers (batting average, ERA), DM Sans for readable body text, DM Mono for tabular data that needs to align in columns. The dark surface palette is designed for low-light broadcast booths — navy-black backgrounds with high-contrast data.

The component architecture is three pieces: `Panel` (a dark card with header), `StatDisplay` (number + label + optional delta), and `DashboardGrid` (3-column responsive layout). That's it. A broadcast tool doesn't need a component library.

## Commits 6-8: Backend with Opinions

Fastify 5 over Express isn't just a speed argument (though it's 2-3x faster on benchmarks). Fastify gives you JSON Schema validation on routes out of the box. Every request and response has a schema. If the broadcast tool sends malformed data, you find out at the boundary — not three layers deep in a service.

```typescript
import Fastify from "fastify";
import pino from "pino";

const server = Fastify({
  logger: pino({ level: "info" }),
});

server.get("/health", {
  schema: {
    response: {
      200: {
        type: "object",
        properties: {
          status: { type: "string" },
          timestamp: { type: "string" },
        },
      },
    },
  },
  handler: async () => ({
    status: "healthy",
    timestamp: new Date().toISOString(),
  }),
});
```

The SQLite schema is three tables: `cohost_profiles` (who's in the booth tonight), `narrative_log` (story threads to reference during broadcast), and `preferences` (display settings per host). WAL mode is non-negotiable:

```sql
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
```

WAL means readers never block writers. During a live broadcast, the frontend can poll for updates while the backend writes new Statcast data. No locks. No contention.

### Single Source of Truth

One decision that pays dividends across every service:

```json
{
  "teamId": 144,
  "teamName": "Atlanta Braves",
  "abbreviation": "ATL",
  "league": "NL",
  "division": "East",
  "stadium": {
    "name": "Truist Park",
    "coordinates": { "lat": 33.8911, "lon": -84.4681 },
    "elevation_ft": 1050
  },
  "parkFactors": {
    "overall": 97,
    "hr": 95,
    "h": 99
  },
  "brand": {
    "primary": "#13274F",
    "secondary": "#CE1141",
    "accent": "#EAAA00"
  }
}
```

Every service reads `team-config.json`. The frontend pulls brand colors from it. The backend uses `teamId` for API calls. The Python service uses stadium coordinates for weather lookups. One file, three consumers, zero drift.

## Commit 9: Python Microservice for Data Science

Why not just call the MLB API from Node? Because pybaseball exists. It wraps Statcast, Baseball Reference, and FanGraphs data in clean Python DataFrames. Fighting that with `node-fetch` and manual parsing would be insane.

FastAPI on port 8001 handles exactly one concern: fetching and shaping baseball data. The Node backend calls it when it needs fresh Statcast numbers. Clean boundary, right tool for the job.

## Commit 10: Docker Compose

Three services, all health-checked:

```yaml
services:
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on:
      backend:
        condition: service_healthy

  backend:
    build: ./backend
    ports: ["3001:3001"]
    volumes:
      - sqlite_data:/app/data
      - ./backend/team-config.json:/app/team-config.json:ro
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3001/health"]
      interval: 10s
      timeout: 3s
      retries: 3
    depends_on:
      python-service:
        condition: service_healthy

  python-service:
    build: ./python-service
    ports: ["8001:8001"]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  sqlite_data:
```

The SQLite database lives on a named volume. Container restarts don't lose data. The `team-config.json` is bind-mounted read-only — the backend reads it but never writes it. Health checks cascade: Python starts first, backend waits for Python, frontend waits for backend.

A `Makefile` wraps the common operations: `make dev`, `make test`, `make lint`, `make typecheck`, `make clean`. Nobody should have to remember Docker Compose flags.

## Commit 11: CI Pipeline

Four parallel GitHub Actions jobs: frontend (build + typecheck + lint), backend (test + typecheck + lint), python (test + lint), docker-build (compose build to verify Dockerfiles aren't broken). They run independently because they share no state. A CSS typo in the frontend shouldn't block backend tests.

Total time from empty repo to green CI: one working session.

## Side Quest: CAD Agent License Gating and DWG Support

The other 19 commits went to [cad-dxf-agent](https://github.com/jeremylongshore/cad-dxf-agent). Three PRs shipped:

**PR #58 — Titleblock auto-detection.** Engineering drawings have title blocks (the bordered info box in the corner). Our comparison engine was flagging title block text as "changes" when it wasn't. Now the system auto-detects title blocks by scanning for entities on TITLE, SEAL, REVISION, and BORDER layers, then injects them as exclusion regions. If a profile excludes more than 80% of entities, it warns you — that's almost certainly misconfigured.

**PR #59 — License gate + DWG support.** Two features that sound unrelated but shipped together because they both touch the auth boundary. The license check hits Firestore with a 5-minute cache and fails closed — if the license service is down, access is denied. Every authenticated endpoint goes through `get_licensed_user()`. DWG uploads now work via server-side ODA File Converter with SHA-256 checksum verification on the converter binary. Gemini code review caught two issues: guard empty UID with an early 403, and wrap synchronous Firestore calls in `run_in_threadpool`.

**PR #60 — Close 10 remaining beads.** Backend got file hashes in bundle metadata, alignment results saved to bundles, match explanations with feature scores, diff summaries with per-layer counts, and xref/dynamic block detection. The frontend revision wizard got fully wired: profile selector with DWG support, alignment preview with confidence bars, per-operation approve/reject with bulk actions, and full keyboard navigation with ARIA roles. 1,150 tests pass.

## The Pattern

This was a 30-commit day across two very different projects. One greenfield, one mature. What they share: strong opinions about tooling, specs before code, and CI that runs before you merge.

The braves dashboard went from nothing to a running 3-service Docker Compose stack with CI in one session. Not because of any framework magic. Because every choice was deliberate: SQLite over Postgres (right tool for single-user broadcast), Fastify over Express (schemas at the boundary), Tailwind v4 over Tailwind v3 (CSS-first config), a Python microservice instead of cramming pybaseball into Node.

Speed comes from not deliberating. Pick your tools, commit to them, build forward.

---

## Related Posts

- [Building a Deterministic DXF Comparison Engine in One Day](/blog/deterministic-dxf-comparison-engine-one-day-build/) — the same cad-dxf-agent project, earlier in its lifecycle
- [Building a Complete React Native Mobile App in One Session](/blog/react-native-mobile-app-one-session/) — another zero-to-done build with opinionated stack choices
- [Production Release Engineering: Shipping v4.5.0](/blog/production-release-engineering-v450/) — what CI looks like at scale with 38 commits and 739 skills
