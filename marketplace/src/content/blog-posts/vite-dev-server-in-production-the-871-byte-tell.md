---
title: "Vite Dev Server in Production: The 871-Byte Tell"
description: "scorecardecho.com shipped the Vite dev server to every visitor. Three signals catch it in a minute; a multi-stage Dockerfile fixes it for any SPA container."
date: "2026-05-27"
tags: ["vite", "docker", "production", "diagnostics", "frontend"]
featured: false
canonical: "https://startaitools.com/posts/vite-dev-server-in-production-the-871-byte-tell/"
---

## The 871-byte tell

A user reported scorecardecho.com was slow and "had to be refreshed" to render. The site fronts a React SPA behind Caddy, behind Docker Compose, behind a single VPS — a stack that had been "fine" for months. One `curl -s https://scorecardecho.com/ | head -40` answered the ticket in under a minute. The HTML shell was 871 bytes. It contained `<script type="module" src="/@vite/client">`, `/@react-refresh`, and a literal `src="/src/main.tsx"` reference. That output is not a production response. That is the Vite dev server, exposed straight to the public internet, transpiling raw TypeScript per-request for every visitor.

## Three smoking guns (the 60-second checklist)

Each signal below is independent. Any one of them is enough to know. All three together is diagnosis-complete.

**Signal 1 — the container's own CMD.** Inspect what the running image was actually told to do:

```bash
docker inspect frontend --format '{{.Config.Cmd}}'
# [npm run dev -- --host]
```

A production container has no business running `npm run dev`. That string is the smoking gun in the container definition itself, surviving every restart.

**Signal 2 — the port mapping.** Compose binds the framework's default development port:

```bash
docker compose ps
# frontend ... 127.0.0.1:5173->5173/tcp
```

Vite's dev port is 5173. Next.js dev is 3000. CRA is 3000. webpack-dev-server is 8080. If the port mapping matches a framework default-dev port (not a chosen runtime port like 80 or 8080-for-nginx), the container was built from a dev recipe.

**Signal 3 — the HTML payload.** The framework injects dev-only client scripts into the page shell. One grep tells the whole story:

```bash
curl -s https://scorecardecho.com/ | \
  grep -E '@vite/client|@react-refresh|webpack-hmr|src/main'
# <script type="module" src="/@vite/client"></script>
# <script type="module">import RefreshRuntime from "/@react-refresh" ...
# <script type="module" src="/src/main.tsx?t=1748394610234"></script>
```

A built bundle has none of these. A dev server cannot avoid them — they are the runtime hooks that HMR depends on.

## Why this happens

The Dockerfile was a single-stage `node:22-slim` image with `CMD ["npm", "run", "dev", "--", "--host"]`. It worked on a laptop. Someone (the project's own past self) copied it into production months ago because the site rendered, the port forwarded, and Caddy in front returned `200 OK` on every probe. Compose layered on two volume mounts — `./frontend/src:/app/src` and `./frontend/index.html:/app/index.html` — which made HMR-driven local development feel instant. In production, those same mounts shadowed any `dist/` directory the container might have built, guaranteeing the dev server was the only thing that could ever serve a request. Nothing alarmed because nothing was failing — the site was just doing transpile-on-demand for every visitor, every page load, forever.

## The fix: a two-stage Dockerfile

The new `frontend/Dockerfile` builds the SPA in one stage and serves the static `dist/` in a second:

```dockerfile
-FROM node:22-slim AS base
+FROM node:22-slim AS build
 WORKDIR /app

 COPY package.json package-lock.json ./
 RUN npm ci

 COPY . .
+RUN npm run build
+
+FROM node:22-slim AS runtime
+WORKDIR /app
+
+# `serve` is a tiny static file server with built-in SPA fallback
+# (rewrites every unknown path to /index.html via `-s`).
+RUN npm install -g serve@14
+
+COPY --from=build /app/dist ./dist

 EXPOSE 5173
-CMD ["npm", "run", "dev", "--", "--host"]
+CMD ["serve", "-s", "dist", "-l", "5173", "-L"]
```

Three flags carry the load. `-s` is "single-page application" mode: any path that does not resolve to a real file in `dist/` rewrites to `/index.html`, so the React Router routes survive a hard refresh. `-l 5173` keeps the listen port identical to the dev configuration — every upstream piece (Caddy block on the VPS, compose port map, internal service name) keeps working with zero coordinated change. `-L` is `serve`'s `--no-request-logging` switch; it suppresses the per-request log line the process would otherwise emit, which keeps the container's stdout channel quiet enough that real anomalies (a sudden burst of 4xxs, a backend exception leaking through) are not buried under access-log noise. The port was kept deliberately. Picking 80 or 3000 would have meant editing the Caddyfile and the compose file in the same deploy — a coordinated change for no benefit. Keeping 5173 made the switch a one-file diff at the perimeter.

## The compose change

The two source-mount volumes had to go:

```yaml
   frontend:
     build: ./frontend
     restart: unless-stopped
+    # Production: built static bundle served by `serve` (no dev server).
     environment:
       - VITE_BACKEND_URL=http://backend:3001
     ports:
       - "127.0.0.1:5173:5173"
-    volumes:
-      - ./frontend/src:/app/src
-      - ./frontend/index.html:/app/index.html
```

Those mounts are HMR-essential in development — they are how a file save on the host instantly reflects in the running container. In production they actively shadow whatever the multi-stage image built into `/app/dist`. Without removing them, the new build stage would still produce a real bundle, the runtime stage would still copy it into `dist/`, and then compose would lay raw source files right back over the top of the runtime filesystem the instant the container started. The container would silently revert to transpile-on-demand from the mounted source — same behavior as before, just with extra build time and a confused operator wondering why the fix did not take. Removing the volumes is half the fix; the Dockerfile is the other half. Neither one in isolation would have worked.

## Verification: predicted before / after

| Signal | Before (Vite dev server) | After (built bundle) |
|---|---|---|
| SPA shell HTML | ~871 bytes (dev injects `/@vite/client`, `/@react-refresh`, `src/main.tsx`) | ~250 bytes (minified `index.html`) |
| JS payload | N raw `.tsx` modules, transpiled per-request | one minified bundle |
| Container memory | ~136 MB (Node + Vite process) | ~30 MB (just `serve`) |
| TTFB on `/` | ~370 ms | single-digit ms (Caddy → `serve` ≈ sendfile) |
| HMR WebSocket | attempted; periodically renders blocked | no WebSocket at all |

The HMR WebSocket line is the one users were feeling. Vite's client repeatedly tried to attach an HMR socket through Caddy, which had no `handle` block for the upgrade. The attempt eventually timed out, sometimes mid-render, leaving the page partly hydrated — which is the exact "have to refresh" symptom that surfaced the bug.

## What would have caught this earlier

Three of the five rows in the verification table are observable from outside the container, which means every one of them is automatable as a deploy-time smoke test. A post-deploy GitHub Actions step running against the public URL would have failed loudly on day one of the misconfiguration:

```bash
# Fail the deploy if the production shell still contains dev-mode hooks.
HTML=$(curl -fsSL "https://scorecardecho.com/")
echo "$HTML" | grep -qE '@vite/client|@react-refresh|webpack-hmr|sockjs-node' && {
  echo "FAIL: production HTML contains dev-server hooks" >&2
  exit 1
}

# Sanity-check the shell size. A built SPA index.html for a small site
# lands in the low hundreds of bytes; a dev-injected shell is consistently
# north of 700. Tune THRESHOLD to your own built index.html size + headroom
# (this site's built shell is ~250 bytes, dev-injected was 871 — 600 is the
# midpoint with room to grow before the threshold itself needs revisiting).
THRESHOLD=600
SIZE=$(printf '%s' "$HTML" | wc -c)
if [ "$SIZE" -gt "$THRESHOLD" ]; then
  echo "FAIL: shell HTML is ${SIZE} bytes (> ${THRESHOLD}) — looks dev-injected" >&2
  exit 1
fi
```

Six lines of shell, run once after every deploy, would have caught the regression the same hour it landed instead of waiting for a user to file a "feels slow" ticket months later. The smoke test does not require introspection inside the container; it does not need access to the VPS; it does not need credentials. It treats the production URL as the contract and asserts the contract holds. That is the cheapest possible enforcement layer, and it is the layer that should have existed from the first deploy.

## The transferable lesson

The three-signal checklist works on every Node-based SPA container, not just Vite ones. Next.js dev injects `/_next/static/chunks/webpack.js` with an HMR client. CRA dev injects `webpack-dev-server/client/index.js?protocol=ws`. webpack-dev-server in any flavor injects `/sockjs-node`. The signature is always the same: framework injects dev-only HMR client into the HTML shell, default dev port is exposed on the host, the CMD line still says "dev." Run `curl -s https://<your-site>/ | grep -E '@vite/client|webpack-hmr|_next/static/chunks/webpack|sockjs-node|src/main\.(tsx|jsx)'` against your own production URL right now. If any line comes back, the container is shipping its dev server to every visitor, and the fix is a multi-stage Dockerfile that costs nothing but stays structurally invisible until somebody looks.
