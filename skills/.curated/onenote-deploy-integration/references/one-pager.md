# OneNote Deploy Integration — One-Pager

## The Problem

Deploying OneNote integrations to containers breaks the local development experience in three critical ways: MSAL token caches are in-memory by default and vanish on every container restart (forcing re-authentication), health check endpoints that return HTTP 200 without verifying Graph API connectivity mask silent failures, and abrupt container termination loses auth state — requiring users to re-authenticate on every deploy. Multi-replica deployments compound this because each replica maintains its own token cache.

## The Solution

Production-ready container deployment with MSAL token cache persistence (file-based for single replica, Redis for multi-replica), health and readiness endpoints that validate actual Graph API connectivity, and graceful shutdown handlers that flush token state on SIGTERM. Includes Dockerfile, Docker Compose, and Kubernetes manifests with proper probes.

## Who / What / When / Where / Why

| | |
|---|---|
| **Who** | DevOps engineers and backend developers deploying OneNote integrations |
| **What** | Container deployment with MSAL token persistence, health checks, and graceful shutdown |
| **When** | Moving OneNote integrations from local development to staging or production |
| **Where** | Docker, Docker Compose, Kubernetes, any container orchestrator |
| **Why** | MSAL in-memory token cache does not survive container restarts, health checks must validate the full Graph API path, and shutdown must preserve auth state |

## Key Differentiators

- Health check validates actual Graph API reachability, not just HTTP liveness
- Two token cache strategies: file-based (simple) and Redis (multi-replica) with code for both
- SIGTERM handler flushes token cache before exit with 10s forced-exit safety net
- Kubernetes manifest includes proper liveness/readiness probes tuned for MSAL token acquisition timing

## Stack

| Component | Technology |
|-----------|-----------|
| API | Microsoft Graph v1.0 |
| Auth | MSAL (delegated) |
| SDK (Python) | msgraph-sdk + azure-identity |
| SDK (Node) | @microsoft/microsoft-graph-client + @azure/identity |
| Container | Docker multi-stage build |
| Cache | Redis 7 or file-based |
| Orchestration | Docker Compose / Kubernetes |
