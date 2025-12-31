# exa-incident-runbook

## Skill Scaffold

```
exa-incident-runbook/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Execute rapid incident response for Exa outages with triage, mitigation, fallback activation, and communication templates.
**Workflow:** On-call response skill - minimizes MTTR during Exa incidents.
**Relates to:** Follows exa-observability; uses patterns from exa-reliability-patterns

## Summary

This skill provides incident response procedures: P1/P2/P3 incident classification for Exa issues, initial triage steps (check Exa status page, verify API key, test connectivity), fallback activation procedures (cached results, degraded search), stakeholder communication templates, evidence collection for post-incident analysis, escalation paths to Exa support, and post-incident review process. Target: <15 minute MTTR for P1 Exa incidents with graceful degradation.
