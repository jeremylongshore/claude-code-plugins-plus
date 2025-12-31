# retellai-prod-checklist

> Execute production deployment checklist including pre-flight checks, agent testing, and rollback procedures

## Directory Structure

```
retellai-prod-checklist/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for production deployment checklist |
| examples/example.py | Python | Example pre-flight validation and health check scripts |

## Summary

**Category:** operations
**Target Audience:** DevOps engineers, Release managers, SREs
**Trigger Phrases:** `retell production`, `deploy retell`, `retell go-live`, `retell launch checklist`

### What This Skill Does

This skill provides a comprehensive production deployment checklist for Retell AI voice agents. It covers pre-flight checks (agent configuration validation, voice availability), staged rollout procedures, health check implementation, monitoring setup verification, and documented rollback procedures for quick recovery.

### Technical Success Criteria

- All pre-flight checks passing
- Agent deployed and responding to calls
- Health checks functional and alerting
- Monitoring dashboards active
- Rollback procedure tested and documented

### Business Success Criteria

- Zero-downtime deployments
- Reduced production incidents
- 100% deployment success rate with instant rollback capability

## Related Skills

- retellai-ci-integration - Automated deployment pipelines
- retellai-observability - Monitoring setup
- retellai-incident-runbook - Incident response
