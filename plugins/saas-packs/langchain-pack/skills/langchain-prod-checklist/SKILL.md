---
name: langchain-prod-checklist
description: |
  Execute LangChain production deployment checklist.
  Use when preparing for production launch, validating deployment readiness,
  or auditing existing production LangChain applications.
  Trigger with phrases like "langchain production", "langchain prod ready",
  "deploy langchain", "langchain launch checklist", "production checklist".
allowed-tools: Read, Write, Edit, Bash(python:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Production Checklist

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive checklist for deploying LangChain applications to production with reliability, security, and performance.

## Prerequisites
- LangChain application developed and tested
- Infrastructure provisioned
- CI/CD pipeline configured

## Instructions

### 1. Configuration & Secrets
1. All API keys in secrets manager (not env vars in code)
2. Environment-specific configurations separated
3. Configuration validation on startup with `pydantic_settings.BaseSettings`

### 2. Error Handling & Resilience
4. Retry logic with exponential backoff
5. Fallback models: `primary.with_fallbacks([fallback])`
6. Circuit breaker for cascading failures

### 3. Observability
7. Structured logging, Prometheus metrics, LangSmith tracing
8. Alerting rules for error rate and latency

### 4. Performance
9. Redis caching for repeated queries
10. Connection pooling, timeout limits, batch processing

### 5. Security
11. Input validation (length limits, sanitization)
12. Rate limiting per user/IP, audit logging

### 6. Testing
13. Unit tests for all chains, integration tests with mock LLMs
14. Load tests and chaos engineering

### 7. Deployment
15. Health check endpoint, graceful shutdown, rolling deployment
16. Rollback procedure documented

### 8. Cost Management
17. Token counting, usage alerts, budget limits

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for code examples and deployment validation script.

## Output
- Validated production configuration
- Health check endpoint
- Pre-deployment validation script
- Cost estimation utilities

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| API key missing | Bad secrets config | Validate on startup |
| LLM timeout | Network/provider issue | Set timeout + fallback |
| Cache miss storm | Redis down | Graceful degradation |

## Examples


**Basic usage**: Apply langchain prod checklist to a standard project setup with default configuration options.

**Advanced scenario**: Customize langchain prod checklist for production environments with multiple constraints and team-specific requirements.

## Resources
- [LangChain Production Guide](https://python.langchain.com/docs/guides/productionization/)
- [LangSmith](https://docs.smith.langchain.com/)
- [Twelve-Factor App](https://12factor.net/)

## Next Steps
After launch, use `langchain-observability` for monitoring.