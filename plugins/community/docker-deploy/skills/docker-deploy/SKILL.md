---
name: docker-deploy
description: |
  When the user asks you to containerize an application, write a Dockerfile,
  set up a docker-compose stack, or deploy with Docker.

  Trigger phrases:
  - "dockerize this"
  - "create a Dockerfile"
  - "deploy with docker"
  - "docker-compose setup"
  - "build a container"
  - "containerize my app"
  - "multi-stage build"
  - "set up compose"
  - "docker deployment"
  - "push this image"
allowed-tools: Bash, Read, Write, Edit, Glob
version: 1.0.0
author: Carl Johnson <gupsspam@users.noreply.github.com>
license: MIT
compatibility: agentskills.io/specification
tags: [docker, deployment, containers, devops, infrastructure, docker-compose, ci-cd]
---

# Docker Deploy

## Overview

This skill teaches Claude Code how to production-ize any application with Docker: writing secure, layered Dockerfiles; composing multi-service stacks with `docker-compose.yml`; building and tagging images with best-practice layer caching; managing registry pushes and pulls; and running containers with proper resource limits, health checks, networking, and volume mounts. It covers the full lifecycle from a bare project to a running, production-grade containerized deployment.

The core philosophy is **layers are cache units, and every RUN is a layer**: Dockerfiles are organized so that expensive, infrequently-changed steps (system dependencies, pip install) come first and application code comes last. This gives sub-second rebuilds on code changes while keeping security hygiene such as running as non-root, pinning base image digests, and excluding secrets from image layers.

## Prerequisites

- **Docker Engine 24+** installed and running (`docker info` to verify). On Linux, the calling user must be in the `docker` group (or commands must be prefixed with `sudo`).
- **docker-compose plugin v2+** (`docker compose version` — the standalone `docker-compose` is deprecated and should not be used).
- **For registry operations:** `docker login` credentials configured for the target registry (Docker Hub, GHCR, ECR, etc.). Use `docker login <registry>` to authenticate fresh; credentials are stored in `~/.docker/config.json`.
- **For the project being containerized:** A clear understanding of the runtime language/framework (Node.js, Python, Go, Rust, etc.) so the correct base image and install steps can be chosen. If you're unsure, inspect `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, or `Makefile` to determine the runtime.
- **A `.gitignore` or `.dockerignore` is mandatory for production builds** — the build context is sent to the Docker daemon, and stray `node_modules/` or `__pycache__` directories bloat layers and invalidate caches. The skill creates one if none exists.
- **Minimum free disk space** for images: check with `df -h /var/lib/docker` — standard images are 100 MB–1 GB each; builds can temporarily double that.

## Instructions

1. **Inspect the project.** Run `ls -la` and identify key files: the package manager manifest (`package.json`, `requirements.txt`, `Cargo.toml`, `go.mod`, `pyproject.toml`, `Gemfile`), entrypoint files (`main.py`, `index.js`, `app.py`, `main.go`, `server.ts`), and existing infra config (`Dockerfile`, `docker-compose.yml`, `.dockerignore`, `Makefile`). Report the project type and any existing container setup to the user.

2. **Determine the base image.** Choose the official slim variant of the language runtime matching the project's major version:
   - **Node.js:** `node:<major>-alpine` (e.g. `node:20-alpine`)
   - **Python:** `python:<major.minor>-slim` (e.g. `python:3.12-slim`); prefer `-slim` over `-alpine` for Python wheels compatibility unless the project has no native extensions
   - **Go:** `golang:<major>-alpine` for builder, `alpine:3.20` or `gcr.io/distroless/base` for the runtime stage
   - **Rust:** `rust:<major>-slim` for builder, `debian:bookworm-slim` or distroless for runtime
   - **Static site:** `nginx:alpine` or `caddy:alpine`
   - **Java / JVM:** `eclipse-temurin:<major>-jre-alpine` (runtime) and `eclipse-temurin:<major>-jdk-alpine` (build, if needed)
   - Always pin the **major.minor.patch digest** for repeatable builds: after selecting the tag, resolve it with `docker pull <image>:<tag> && docker inspect <image>:<tag> --format '{{.RepoDigests}}'` or pin `FROM <image>:<tag>@sha256:<digest>`.

3. **Create `.dockerignore`.** At the project root, write a `.dockerignore` that excludes everything that shouldn't be in the build context:
   ```
   .git
   .gitignore
   .env
   .env.*
   node_modules
   __pycache__
   *.pyc
   .venv
   venv
   .pytest_cache
   *.log
   .idea
   .vscode
   *.swp
   Dockerfile
   .dockerignore
   README.md
   ```
   Add project-specific entries based on what `ls -la` and `.gitignore` show. Read the existing `.gitignore` if it exists and mirror its ignore patterns for build-time artifacts.

4. **Write the Dockerfile — order layers for cache efficiency.** Structure the Dockerfile so that frequently-changing content (application code) goes last:

   ```dockerfile
   # syntax=docker/dockerfile:1
   FROM node:20-alpine AS builder
   WORKDIR /app
   COPY package*.json ./
   RUN npm ci --only=production
   COPY . .
   RUN npm run build

   FROM node:20-alpine AS runner
   WORKDIR /app
   RUN addgroup --system app && adduser --system --ingroup app app
   COPY --from=builder /app/dist ./dist
   COPY --from=builder /app/node_modules ./node_modules
   COPY package*.json ./
   USER app
   EXPOSE 3000
   HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
     CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
   CMD ["node", "dist/index.js"]
   ```

   **Rules for every Dockerfile you write:**
   - Always set `WORKDIR` explicitly — never rely on the default `/`.
   - Always create and switch to a **non-root user** in the final stage. Use `addgroup`/`adduser` on Alpine and `groupadd`/`useradd` on Debian-based images.
   - Copy dependency manifests **before** code (`COPY package*.json ./` before `COPY . .`) so `npm install` / `pip install` is cached unless the manifest changes.
   - Use `--link` with `COPY` for independent cache invalidation (`COPY --link` creates a separate cache mount for that layer).
   - Prepend `RUN --mount=type=cache` for package manager caches where possible (`/root/.cache/pip`, `/root/.npm`, `/go/pkg/mod`) — but only when the Docker build supports BuildKit (always true for Docker 24+, verify with `docker buildx version`).
   - Always include both `EXPOSE` (documentation) and `HEALTHCHECK` (runtime verification).
   - Use `CMD` in exec form (`["executable", "arg"]`), not shell form, to handle signals correctly.

5. **Handle framework- and language-specific patterns:**

   - **Node.js / npm:** Use `npm ci` instead of `npm install` for deterministic installs; if a lockfile is absent, run `npm install` but warn the user to commit the lockfile. For monorepos, use `COPY --parents` or separate Dockerfiles per workspace.
   - **Python / pip:** Pin requirements with `pip install --no-cache-dir -r requirements.txt`; use `pip install --no-cache-dir -e .` for local packages; prefer `poetry export -f requirements.txt > requirements.txt` if `pyproject.toml` with Poetry is found.
   - **Go:** Use `COPY go.mod go.sum ./ && RUN go mod download` for cache separation, then `COPY . . && RUN CGO_ENABLED=0 go build -o /app/server .` for a fully static binary.
   - **Rust / Cargo:** Similarly separate `COPY Cargo.toml Cargo.lock ./ && RUN cargo fetch` before `COPY src ./ && RUN cargo build --release`.
   - **Static sites:** Two-stage: builder stage generates the site (e.g. `npm run build`), final stage is `FROM nginx:alpine` and copies the static output into `/usr/share/nginx/html`. Include an `nginx.conf` for SPA routing if needed (e.g. `try_files $uri $uri/ /index.html`).

6. **Set sensible resource constraints.** In the Dockerfile comment or in a docker-compose.yml, document recommended limits. Apply them when running:

   ```bash
   docker run -d --name myapp \
     --memory="512m" --cpus="0.5" \
     --restart=unless-stopped \
     -p 3000:3000 \
     myapp:latest
   ```

   For production, add `--memory-reservation="256m"` so the kernel reclaims memory under pressure. Never run containers without `--restart` in production — the container will stop on crash and not recover.

7. **Create `docker-compose.yml` for multi-service stacks.** If the project uses a database, cache, queue, or other backing service, write a compose file:

   ```yaml
   version: "3.9"
   services:
     app:
       build:
         context: .
         dockerfile: Dockerfile
       ports:
         - "127.0.0.1:3000:3000"
       environment:
         - NODE_ENV=production
         - DATABASE_URL=postgres://user:pass@db:5432/myapp
       env_file:
         - .env.production
       depends_on:
         db:
           condition: service_healthy
       restart: unless-stopped
       healthcheck:
         test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/health"]
         interval: 30s
         timeout: 3s
         retries: 3
         start_period: 10s

     db:
       image: postgres:16-alpine@sha256:<pinned-digest>
       volumes:
         - pgdata:/var/lib/postgresql/data
       environment:
         POSTGRES_DB: myapp
         POSTGRES_PASSWORD_FILE: /run/secrets/db_password
       secrets:
         - db_password
       healthcheck:
         test: ["CMD-SHELL", "pg_isready -U myapp"]
         interval: 10s
         timeout: 5s
         retries: 5
       restart: unless-stopped

   volumes:
     pgdata:

   secrets:
     db_password:
       file: ./secrets/db_password.txt
   ```

   **Compose rules:**
   - Bind `127.0.0.1:<port>` (not `0.0.0.0`) for the app service unless reverse-proxying from another container — never expose the app directly to the network without an ingress layer.
   - Use Docker `secrets` for sensitive values passed as files, not environment variables.
   - Always add `depends_on` with `condition: service_healthy` for dependent databases — a hardcoded sleep is fragile.
   - Use named volumes (not bind mounts) for database data so it's managed by Docker and survives container destruction.
   - Pin database images to a specific digest, just like application images.

8. **Build the image with cache-efficient tags.** After writing the Dockerfile, build with:

   ```bash
   docker build -t myapp:latest -t myapp:$(date +%Y%m%d-%H%M%S) .
   ```

   Tag conflations: `myapp:latest` (convenience alias, updated on every deploy), `myapp:YYYYMMDD-HHMMSS` (immutable timestamp for rollback). In CI, also tag with the commit SHA: `myapp:git-<short-sha>`.

   If the build fails, inspect the error (common causes: missing `apt` deps, wrong base image arch, `npm ci` without a lockfile) and fix it before retrying. Do not use `--no-cache` except as a last resort.

9. **Verify the image runs correctly.** Start a disposable container from the built image:

   ```bash
   docker run --rm -d -p 3000:3000 --name myapp-test myapp:latest
   sleep 3
   docker logs myapp-test
   curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/health
   docker stop myapp-test
   ```

   Check that: (a) the container starts without errors, (b) the health endpoint returns 2xx, (c) the logs don't show connection refused or missing env var errors. If the test fails, check `docker logs <name>` and fix the Dockerfile or compose config.

10. **Push to a registry.** After a successful local build and test:

    ```bash
    docker tag myapp:latest registry.example.com/myapp:latest
    docker tag myapp:latest registry.example.com/myapp:YYYYMMDD-HHMMSS
    docker push registry.example.com/myapp:latest
    docker push registry.example.com/myapp:YYYYMMDD-HHMMSS
    ```

    For Docker Hub: tag with `docker.io/username/myapp:<tag>`. For GitHub Container Registry: tag with `ghcr.io/owner/myapp:<tag>`. Always push the timestamp-specific tag first, then `latest` so there's a window to revert if the latest push fails mid-way.

    If `docker push` fails with a 403 or "denied", the user isn't authenticated. Run `docker login <registry>` (or `docker login ghcr.io -u <username> --password-stdin <<< "$GHCR_TOKEN"` for headless auth) and retry.

11. **Pull and restart on the target host.** On the deployment server:

    ```bash
    docker pull registry.example.com/myapp:YYYYMMDD-HHMMSS
    docker stop myapp && docker rm myapp
    docker run -d --name myapp \
      --restart=unless-stopped \
      --memory="512m" \
      --network=host \
      myapp:YYYYMMDD-HHMMSS
    docker image prune -f  # remove old dangling images
    ```

    Prefer a new container (`docker stop && docker rm && docker run`) over `docker restart` — a fresh container gets a clean filesystem and restarted health checks. Use `docker compose up -d` if the stack uses compose.

12. **Set up a private network for inter-container communication.** When the app and database are on the same host, create a dedicated bridge network:

    ```bash
    docker network create myapp-net
    docker run -d --name myapp --network myapp-net ...
    docker run -d --name db --network myapp-net ...
    ```

    Containers on the same user-defined bridge network can reach each other by service name. Docker Compose does this automatically. Never use `--link` (deprecated) or rely on `--network=host` for inter-container communication.

13. **Add a health check endpoint in the application code** if one doesn't exist yet. The app should expose `GET /health` returning `{"status":"ok"}` with HTTP 200. If the app depends on a database, `/health` should also verify the database connection (and return 503 if it's down). Suggest this code change to the user and make it if they agree.

14. **Optimize the final image size.** After the build works, check the image size:

    ```bash
    docker images myapp --format "{{.Repository}}:{{.Tag}}\t{{.Size}}"
    ```

    If the image is over 500 MB for a language runtime, consider:
    - Switching to a distroless runtime stage (`gcr.io/distroless/`) when the binary is fully static.
    - Removing build-time tools in the final stage (don't `COPY --from=builder /usr/lib/gcc`).
    - Using `--mount=type=cache` for package downloads so they don't persist in layers.
    - Running `docker scout` (`docker scout quickview myapp:latest`) to identify CVEs and unnecessary packages.

15. **Clean up dangling resources.** After the build and any test runs, run:

    ```bash
    docker image prune -f      # remove dangling images (<none>:<none>)
    docker container prune -f  # remove stopped containers
    docker builder prune -f    # clean build cache if space is tight
    ```

    Never prune volumes (`docker volume prune`) without explicit user consent — that's persistent data.

16. **Write a one-liner deploy script.** After all steps pass, write a `deploy.sh` at the project root:

    ```bash
    #!/usr/bin/env bash
    set -euo pipefail
    IMAGE_TAG="myapp:$(date +%Y%m%d-%H%M%S)-$(git rev-parse --short HEAD)"
    docker build -t "$IMAGE_TAG" -t myapp:latest .
    docker push "$IMAGE_TAG"
    docker push myapp:latest
    echo "Pushed $IMAGE_TAG"
    # On remote host:
    # ssh deploy@host 'docker pull registry.example.com/myapp:latest && docker compose up -d'
    ```

    Make it executable with `chmod +x deploy.sh`. Adapt the remote-deploy command to match the project's actual SSH target and compose setup.

17. **Document the setup.** Summarize for the user:
    - Which files were created (Dockerfile, .dockerignore, docker-compose.yml, deploy.sh, nginx.conf, etc.)
    - How to build and run: `docker compose up -d`
    - How to rebuild on code changes: `docker compose up -d --build`
    - How to view logs: `docker compose logs -f`
    - How to tear down: `docker compose down -v` (with the `-v` warning about data loss)
    - Where the image is pushed and how to pull it on another host

    If secrets were created, remind the user to keep `secrets/` out of version control and add it to `.gitignore`.

## Output

The following files are created in the project root (existing files are described but not overwritten unless changes are agreed upon):

```
project/
├── Dockerfile           # Multi-stage Dockerfile with caching, non-root user, health check
├── .dockerignore        # Build-context exclusion rules
├── docker-compose.yml   # Multi-service stack with health checks, secrets, named volumes
├── deploy.sh            # Build + tag + push automation script
└── nginx.conf           # (Static sites only) SPA routing config
```

After a successful build and push, the user can verify the running container:

- `docker ps` — shows the running container(s) with uptime and status
- `docker compose ps` — shows all services in the stack
- `curl http://localhost:<port>/health` — returns 200 when healthy
- `docker logs <name>` — application stdout/stderr

The image is pushed to the chosen registry and available for deployment on any host with Docker installed.

## Error Handling

- **`docker: command not found`** — Docker isn't installed. Guide the user to `curl -fsSL https://get.docker.com | sh` (Linux), or refer them to docs.docker.com for macOS/Windows. Verify with `docker --version` after installation.
- **`permission denied` on Docker socket** — The user's shell isn't in the `docker` group. Either `sudo usermod -aG docker $USER && newgrp docker` (and re-login), or prefix every command with `sudo`. Running with `sudo` preserves `$HOME` for `~/.docker/` credentials but requires sudo for the docker group change to take effect.
- **Build fails with `network` / `timeout` / `TLS handshake`** — Docker daemon can't reach external registries. Check `ping google.com` and `docker info | grep "HTTP Proxy"`. On corporate networks, Docker needs proxy config in `~/.docker/config.json` or `/etc/systemd/system/docker.service.d/proxy.conf`.
- **Build fails with `no matching manifest for linux/arm64`** — The base image doesn't support the build machine's CPU architecture. Add `--platform=linux/amd64` to the `FROM` line or switch to a multi-architecture image (tagged `--platform linux/amd64,linux/arm64`). Check the arch with `uname -m`.
- **`docker run` exits immediately** — Run `docker logs <name>` to see stderr. Common causes: missing env vars, the `CMD` binary not found at the WORKDIR path, or the entrypoint script returning non-zero. Start the container interactively to debug: `docker run --rm -it myapp:latest sh`.
- **Container starts but health check fails** — The app might need longer to boot. Increase `start_period` in the HEALTHCHECK. Or the health endpoint may not exist — verify with `docker exec <name> wget -qO- http://localhost:3000/health` (or `curl` if available in the container). If missing, add a `/health` route to the application.
- **`docker push` returns 403 or `denied`** — Not authenticated for that registry. Run `docker login` (or `docker login ghcr.io -u <user>` for GHCR). For CI, use `echo "$PAT" | docker login ghcr.io -u <user> --password-stdin`.
- **`docker compose up` fails with `service "app` depends on service "db" which is undefined`** — Typo in `depends_on` or the service name doesn't match a top-level service key. Check service names match exactly.
- **`port is already allocated`** — The host port is in use. Run `ss -tlnp | grep <port>` to find the conflicting process, or change the host port mapping (e.g. `127.0.0.1:3001:3000`).
- **Disk filling up** — Old images and build cache accumulate. Run `docker system df` to inspect, then `docker image prune -a` (removes all images not used by a container — ask first, this can destroy rollback candidates). Consider a clean-up cron: `docker system prune -f --filter "until=24h"`.
- **Secrets leak into image layers** — If `build` previously ran without `.dockerignore` and a `.env` or `secrets/` was in the build context, those files are baked into intermediate layers. Advice: rebuild with `--no-cache` and invalidate any pushed tags. Then add `.env` and `secrets/` to `.dockerignore` so it can't happen again.

## Examples

### Example 1: "Dockerize this Python FastAPI app"

Starting from a project with `main.py`, `requirements.txt`, and `pyproject.toml`:

1. Inspect `requirements.txt` to confirm FastAPI + uvicorn, and `main.py` to find the app object (`app = FastAPI()`).
2. Write `.dockerignore` mirroring `.gitignore` patterns plus `__pycache__`, `.venv`, and `*.pyc`.
3. Write a two-stage Dockerfile:
   - **Builder:** `FROM python:3.12-slim`, `WORKDIR /app`, `COPY requirements.txt .`, `RUN pip install --no-cache-dir -r requirements.txt`, `COPY . .`
   - **Runner:** `FROM python:3.12-slim`, `WORKDIR /app`, copy installed packages and code from builder, `RUN adduser app`, `USER app`, `EXPOSE 8000`, `HEALTHCHECK CMD curl -f http://localhost:8000/health || exit 1`, `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`
4. Build: `docker build -t fastapi-app:latest .`
5. Test: `docker run --rm -d -p 8000:8000 fastapi-app:latest` and `curl localhost:8000/health`
6. Write `docker-compose.yml` adding a Postgres 16 service with a named volume, secrets, and `depends_on: db: condition: service_healthy`.
7. Push to GHCR and write `deploy.sh`. Result: two files created, container runs on `:8000`, Postgres auto-starts, health check passes.

### Example 2: "Set up a docker-compose stack for my Node.js app with Redis"

Starting from a project with `package.json`, `server.js`, and a `Dockerfile` already present:

1. Review the existing Dockerfile: fix common issues (no non-root user, no `HEALTHCHECK`, no `.dockerignore`, no layer ordering for `npm ci`).
2. Write `.dockerignore` (node_modules, .env, .git, etc.).
3. Rewrite the Dockerfile with a two-stage build: `node:20-alpine` builder for `npm run build`, `node:20-alpine` runner for the compiled output, non-root user, wget-based health check on port 3000.
4. Create `docker-compose.yml`:
   ```yaml
   services:
     app:
       build: .
       ports: ["127.0.0.1:3000:3000"]
       depends_on:
         redis:
           condition: service_started
     redis:
       image: redis:7-alpine
       volumes:
         - redis_data:/data
   volumes:
     redis_data:
   ```
5. Build, tag, and test: `docker compose up -d`, verify `docker compose ps`, check logs.
6. Note: the Redis `depends_on` is `service_started` (not `service_healthy`) because Redis's health check isn't needed for container startup order (the app should handle Redis being temporarily unavailable). Offer to add a health check if the user prefers stricter ordering.
7. Push images and write `deploy.sh`. Result: two-service stack running, Redis data persisted in a named volume.

### Example 3: "Multi-stage build for a Go gRPC server — make the image tiny"

Starting from a Go project with `go.mod`, `cmd/server/main.go`, and protobuf files:

1. Inspect `go.mod` for the Go version. Choose `golang:1.22-alpine` as the builder and `gcr.io/distroless/base` as the runtime (distroless has no shell, no package manager — minimal attack surface).
2. Write the Dockerfile:
   ```dockerfile
   FROM golang:1.22-alpine AS builder
   WORKDIR /app
   COPY go.mod go.sum ./
   RUN go mod download
   COPY . .
   RUN CGO_ENABLED=0 go build -ldflags="-s -w" -o /app/server ./cmd/server/

   FROM gcr.io/distroless/base
   WORKDIR /
   COPY --from=builder /app/server /server
   EXPOSE 50051
   HEALTHCHECK CMD ["/grpc_health_probe", "-addr=:50051"] || exit 1
   CMD ["/server"]
   ```
3. Note: for gRPC, the health probe is a Go binary that must also be compiled statically and copied in. Offer to write a small `cmd/health/main.go` or use `grpc-health-probe`.
4. Build, check image size with `docker images` — should be ~15–25 MB instead of >1 GB for a full golang image.
5. Run, verify the server starts and listens on `:50051`.
6. Push to registry. Result: a ~20 MB image for the Go gRPC service, statically linked, running as non-root (distroless has no `/bin/sh` or `apt` — much harder to exploit).

## Resources

- [Dockerfile reference](https://docs.docker.com/engine/reference/builder/) — all instructions: FROM, COPY, RUN, CMD, EXPOSE, HEALTHCHECK, USER, WORKDIR, ARG, ENV
- [Best practices for writing Dockerfiles](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/) — layer caching, multi-stage builds, `.dockerignore`, security
- [Docker Compose file reference](https://docs.docker.com/compose/compose-file/) — all service fields: healthcheck, depends_on, secrets, volumes, networks, env_file
- [Docker security — run as non-root](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#user) — why `USER` matters and how to set it up on Alpine vs Debian
- [Distroless base images](https://github.com/GoogleContainerTools/distroless) — Google's minimal runtime images, no shell, no package manager, reduced CVE surface
- [BuildKit cache mounts](https://docs.docker.com/build/cache/) — `--mount=type=cache` for pip, npm, apt, and Go module caches
- [Docker Scout](https://docs.docker.com/scout/) — image vulnerability scanning and optimization suggestions
- [Multi-platform builds](https://docs.docker.com/build/building/multi-platform/) — building for linux/amd64 and linux/arm64 on the same host
- [Health check patterns](https://docs.docker.com/engine/reference/builder/#healthcheck) — endpoint design, startup grace period, retries
- [Awesome Compose](https://github.com/docker/awesome-compose) — reference compose files for Python, Node, Go, Java, Rust, and many backing services
