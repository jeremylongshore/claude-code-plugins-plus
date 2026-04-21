# langchain-deploy-integration — One-Pager

Deploy a LangChain 1.0 / LangGraph 1.0 app to Cloud Run, Vercel, or LangServe correctly — timeouts sized for chain length, cold-start mitigation, SSE anti-buffering, Secret Manager over `.env`.

## The Problem

An engineer ships a working LangGraph agent to Vercel and sees `FUNCTION_INVOCATION_TIMEOUT` on every non-trivial request — the Vercel Python runtime defaults to a **10-second** timeout while a three-tool agent easily runs 20-40s (P35). Moving to Cloud Run escapes the wall but introduces a **5-15s cold start** from Python + LangChain + tiktoken + embedding imports, which makes p99 latency 10x p95 (P36). The SSE stream that worked locally hangs forever in production because Nginx and Cloud Run buffer the final `end` chunk (P46). Meanwhile `.env` files copied into the container leak every API key to anyone who can run `docker exec <pod> env` (P37).

## The Solution

This skill walks a multi-stage Dockerfile (slim runtime, `uvicorn`, non-root user) into Cloud Run with `--min-instances=1 --cpu-boost --timeout=3600 --concurrency=80` and CPU-always-allocated billing; a Vercel `vercel.json` with `maxDuration: 60` plus a streaming response that beats the wall-clock cap; a LangServe `add_routes(app, chain, path="/chat")` + FastAPI `lifespan` for connection-pool cleanup; SSE anti-buffering headers (`X-Accel-Buffering: no`, `Cache-Control: no-cache`) to survive reverse proxies; and Secret Manager / `pydantic.SecretStr` for runtime credentials instead of `.env`. Includes a platform decision table (Cloud Run / Vercel Python / Fly.io / Railway / self-hosted) covering timeout cap, cold-start profile, SSE behavior, and per-month cost for a baseline agent.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Python engineers shipping a working LangChain 1.0 / LangGraph 1.0 app to prod on Cloud Run, Vercel, Fly.io, LangServe, or FastAPI behind any reverse proxy |
| **What** | Multi-stage Dockerfile template, `gcloud run deploy` flag set, `vercel.json` with streaming, LangServe + FastAPI lifespan, SSE anti-buffering headers, Secret Manager pattern with `SecretStr`, platform decision table, 4 references (cloud-run, vercel-python, langserve-patterns, dockerfile-and-secrets) |
| **When** | Prepping first prod deploy, debugging a stream that hangs behind a proxy, diagnosing p99 latency spikes, or rotating `.env` secrets into a real secret store |

## Key Features

1. **Timeouts sized for chain length, not HTTP defaults** — Vercel `maxDuration: 60` (vs 10s default) plus streaming-as-mitigation; Cloud Run `--timeout=3600 --concurrency=80` so a LangGraph agent with four tool rounds does not trip `FUNCTION_INVOCATION_TIMEOUT` or a 504
2. **Cold-start mitigation playbook** — `--min-instances=1 --cpu-boost`, CPU-always-allocated billing so background `astream` completes, slim base image, deferred imports of `tiktoken` and embedding models so the 5-15s Python + LangChain load does not land in p99 user latency
3. **SSE-safe proxy configuration** — `X-Accel-Buffering: no`, `Cache-Control: no-cache`, `Content-Type: text/event-stream`, disabled response buffering on Cloud Run / Nginx / Cloudflare so the final `end` event actually reaches the client and `LangGraph.astream` does not hang

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
