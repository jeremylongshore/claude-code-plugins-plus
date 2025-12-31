# exa-reference-architecture

## Skill Scaffold

```
exa-reference-architecture/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Implement production-ready reference architecture with search service layer, caching, error handling, and health checks.
**Workflow:** Architecture guidance skill - provides blueprint for new Exa integrations.
**Relates to:** Follows exa-sdk-patterns; provides foundation for all production deployments

## Summary

This skill provides a reference architecture for Exa integrations: layered service structure (client, cache, search service, API), singleton client configuration, caching layer (query-to-results mapping), error boundary and fallback handling, health check endpoint for Exa connectivity, structured logging with correlation IDs, configuration management pattern, and testing strategy (unit, integration, e2e). Includes starter templates for Node.js and Python.
