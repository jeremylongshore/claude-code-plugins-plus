# Dockerfile and Secrets Reference

A hardened multi-stage Dockerfile and the secret-management boundary between
the platform (Secret Manager, Vercel Secrets) and the Python process
(`pydantic.SecretStr`). Design goal: if someone gets `docker exec` on the
running container, they see **no plaintext API keys** in `env` output (P37).

## Multi-stage Dockerfile

```dockerfile
# syntax=docker/dockerfile:1.7
ARG PY_VERSION=3.12

# ---- builder: compile wheels from locked deps ----
FROM python:${PY_VERSION}-slim AS builder
WORKDIR /build
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
# Export to requirements.txt so the runtime layer doesn't need uv
RUN uv export --format requirements-txt --no-hashes --no-dev > requirements.txt \
 && pip wheel --wheel-dir=/wheels -r requirements.txt

# ---- runtime: minimal, non-root ----
FROM python:${PY_VERSION}-slim AS runtime
# Security: non-root user with fixed UID so volume mounts have stable ownership
RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app
WORKDIR /app

# Install pre-built wheels only; no compiler in the runtime image
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* \
 && rm -rf /wheels /root/.cache

# Copy app last so code changes don't bust the dep layer
COPY --chown=app:app app/ ./app/

# Runtime config
USER app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080
EXPOSE 8080

# uvicorn with 1 worker — Cloud Run handles horizontal scale
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --workers 1"]
```

### Why each choice

| Choice | Reason |
|--------|--------|
| `python:3.12-slim` | ~80 MB vs 900 MB for `python:3.12`. Kills cold start. |
| Multi-stage | Compiler (`gcc`, `build-essential`) stays in builder; runtime has no toolchain. |
| Non-root user (`--uid 10001`) | Defense in depth; some k8s policies refuse `uid=0` containers. |
| `--no-cache-dir` on `pip install` | Saves ~50 MB on runtime image. |
| Single `uvicorn --workers 1` | Cloud Run scales replicas; multi-worker in-process duplicates LangChain memory. |
| `PYTHONUNBUFFERED=1` | Cloud Run / Vercel capture stdout for logs; buffered stdout hides crashes. |

## `.dockerignore` — prevent secret leaks into build context

```
# Secrets — under no circumstances should these enter the image
.env
.env.*
!.env.example
secrets/
*.pem
*.key
*.p12
gcp-sa-*.json

# Dev files that shouldn't ship
.git
.venv
__pycache__
*.pyc
.pytest_cache
.mypy_cache
node_modules
dist
build
```

Build context is uploaded to the daemon wholesale — without
`.dockerignore`, a committed `.env` ends up in the image even if `COPY`
doesn't reference it (it's in the context tarball). CI should scan built
images for `.env` files:

```bash
docker run --rm --entrypoint sh IMAGE -c 'find / -name ".env*" 2>/dev/null'
# Expected output: nothing. Any hit = leak.
```

## Distroless variant (no shell, no debug tools)

When you cannot allow a shell in production (CIS benchmark compliance):

```dockerfile
FROM gcr.io/distroless/python3-debian12:nonroot AS runtime
WORKDIR /app
COPY --from=builder /wheels /wheels
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --chown=nonroot:nonroot app/ ./app/
USER nonroot
ENV PORT=8080 PYTHONUNBUFFERED=1
# Distroless has no /bin/sh — exec form only
CMD ["-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Tradeoff: you lose `docker exec <container> sh` for debugging. Plan your
observability accordingly — structured logs + traces become mandatory.

## Secret Manager on Cloud Run

Three options, in order of preference:

### 1. `--set-secrets=ENV_VAR=secret-name:latest` (simplest)

```bash
gcloud run deploy langchain-api \
  --set-secrets=ANTHROPIC_API_KEY=anthropic-key:latest,OPENAI_API_KEY=openai-key:latest
```

Secret read once at container start, injected as an env var. Rotation
requires a redeploy (Cloud Run does not auto-redeploy on secret version
changes, and `:latest` is resolved at deploy time).

### 2. Mount as a file (for multi-line secrets)

```bash
gcloud run deploy langchain-api \
  --set-secrets=/var/secrets/gcp-key=gcp-sa-key:latest
```

In the app:
```python
import os
os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/var/secrets/gcp-key")
```

### 3. Secret Manager client SDK (for hot rotation)

If you need to pick up secret changes without redeploying, use the client SDK:

```python
from google.cloud import secretmanager
from functools import lru_cache

@lru_cache(maxsize=16)
def get_secret(name: str, version: str = "latest") -> str:
    client = secretmanager.SecretManagerServiceClient()
    path = f"projects/PROJECT/secrets/{name}/versions/{version}"
    return client.access_secret_version(request={"name": path}).payload.data.decode()
```

Clear cache on a signal or after N minutes to pick up rotations. Costs
~$0.03 per 10k access calls — negligible for a cache-hit pattern.

## `pydantic.SecretStr` — the process boundary

Platform secrets land in `os.environ`; wrapping them in `SecretStr` prevents
them from printing in logs, tracebacks, or `repr()` output.

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # env_file=None forces env-only read; prevents reading a stray .env in prod
    model_config = SettingsConfigDict(env_file=None, extra="ignore", case_sensitive=False)

    anthropic_api_key: SecretStr
    openai_api_key: SecretStr
    langsmith_api_key: SecretStr | None = None
    pg_url: SecretStr

settings = Settings()

# Usage: call .get_secret_value() only when handing to an SDK
from langchain_anthropic import ChatAnthropic
model = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key.get_secret_value(),
)

# Accidental prints are safe:
print(settings)
# prints: anthropic_api_key=SecretStr('**********') ...
```

## The `.env` boundary

Dev: `.env` file loaded by `python-dotenv` for convenience.

Prod: **no `.env` file in the image**. Settings read from real env vars
injected by the platform. Enforce with:

```python
# app/settings.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Only read .env locally; never in prod-like envs
        env_file=".env" if os.getenv("ENV", "dev") == "dev" else None,
        extra="ignore",
    )
```

CI lint: grep the built image for `.env`:

```yaml
# .github/workflows/build.yml
- run: |
    docker build -t test-image .
    docker run --rm --entrypoint find test-image / -name ".env*" -type f && {
      echo "::error::.env file found in image"; exit 1
    } || true
```

## Image size targets

| Image | Target | Typical cold-start impact |
|-------|--------|---------------------------|
| `python:3.12` | 1000 MB | +3-5s |
| `python:3.12-slim` + full deps | 400 MB | baseline |
| `python:3.12-slim` + minimal deps | 250 MB | -1s |
| `distroless/python3-debian12` | 180 MB | -2s |

For LangChain apps the dep bloat dominates — `langchain-core`, provider
SDKs, `tiktoken`, and one embedding library easily total 200+ MB. Slim
runtime + no-dev wheels is the realistic target.
