# clade-deploy-integration — One-Pager

Deploy Claude-powered apps to Vercel, Fly.io, or Cloud Run with streaming and proper secrets management.

## The Problem

Deploying an Anthropic integration to production involves platform-specific configuration that is easy to get wrong: secrets stored insecurely, missing CORS headers, function timeouts too short for Claude responses, and no health checks to verify API connectivity after deploy.

## The Solution

This skill provides copy-paste deployment recipes for three major platforms — Vercel Edge Functions, Fly.io containers, and Google Cloud Run — each with secrets management via the platform's CLI, SSE streaming wired end-to-end, and a health check endpoint that confirms Claude connectivity.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Full-stack developers shipping Claude-powered features to production |
| **What** | Platform-specific deploy configs for Vercel, Fly.io, and Cloud Run with streaming, secrets, and health checks |
| **When** | When you have a working local Claude integration and need to deploy it to a production environment |

## Key Features

1. **Vercel Edge Function with SSE** — Complete Next.js App Router route that streams Anthropic responses as Server-Sent Events
2. **Multi-Platform Secrets** — `vercel env add`, `fly secrets set`, and `gcloud --set-secrets` recipes for each platform
3. **Health Check Endpoint** — A lightweight endpoint that makes a real Claude API call to confirm connectivity post-deploy

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
