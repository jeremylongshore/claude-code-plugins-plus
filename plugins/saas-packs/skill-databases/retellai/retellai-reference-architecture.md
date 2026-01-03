# retellai-reference-architecture

> Implement production-ready reference architecture with layered structure, agent management, and health checks

## Directory Structure

```
retellai-reference-architecture/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for reference architecture implementation |
| examples/example.py | Python | Example project structure with layered architecture |

## Summary

**Category:** cicd
**Target Audience:** Architects, Tech leads, Senior developers
**Trigger Phrases:** `retell architecture`, `retell best practices`, `retell project structure`, `how to organize retell`

### What This Skill Does

This skill implements a production-ready reference architecture for Retell AI projects. It covers layered project structure (agents, handlers, integrations), agent management wrapper with caching and health checks, error boundary implementation, environment configuration, and testing patterns for voice agents.

### Technical Success Criteria

- Structured project layout with clear separation
- Agent management wrapper with caching implemented
- Error boundaries preventing cascade failures
- Health checks configured and functional
- Testing patterns established

### Business Success Criteria

- Maintainable codebase for voice AI projects
- Faster onboarding for new team members
- Team adoption of reference architecture within 1 sprint

## Related Skills

- retellai-prod-checklist - Production deployment patterns
- retellai-multi-env-setup - Environment management
- retellai-reliability-patterns - Fault tolerance patterns
