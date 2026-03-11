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
- All API keys in secrets manager (not env vars in code)
- Environment-specific configurations separated
- Configuration validation on startup with `pydantic_settings.BaseSettings`

### 2. Error Handling & Resilience
- Retry logic with exponential backoff
- Fallback models: `primary.with_fallbacks([fallback])`
- Circuit breaker for cascading failures

### 3. Observability
- Structured logging, Prometheus metrics, LangSmith tracing
- Alerting rules for error rate and latency

### 4. Performance
- Redis caching for repeated queries
- Connection pooling, timeout limits, batch processing

### 5. Security
- Input validation (length limits, sanitization)
- Rate limiting per user/IP, audit logging

### 6. Testing
- Unit tests for all chains, integration tests with mock LLMs
- Load tests and chaos engineering

### 7. Deployment
- Health check endpoint, graceful shutdown, rolling deployment
- Rollback procedure documented

### 8. Cost Management
- Token counting, usage alerts, budget limits

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
```python
# Fallback LLM setup
primary = ChatOpenAI(model="gpt-4o-mini", max_retries=3)
fallback = ChatAnthropic(model="claude-3-5-sonnet-20241022")
robust_llm = primary.with_fallbacks([fallback])
```

## Resources
- [LangChain Production Guide](https://python.langchain.com/docs/guides/productionization/)
- [LangSmith](https://docs.smith.langchain.com/)
- [Twelve-Factor App](https://12factor.net/)

## Next Steps
After launch, use `langchain-observability` for monitoring.
