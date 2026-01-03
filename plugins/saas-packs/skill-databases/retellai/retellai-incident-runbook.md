# retellai-incident-runbook

> Execute rapid incident response with triage, mitigation, communication templates, and postmortem procedures

## Directory Structure

```
retellai-incident-runbook/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for incident response procedures |
| examples/example.py | Python | Example diagnostic scripts and communication templates |

## Summary

**Category:** enterprise
**Target Audience:** SREs, On-call engineers, DevOps engineers
**Trigger Phrases:** `retell incident`, `retell outage`, `retell down`, `retell on-call`, `retell emergency`

### What This Skill Does

This skill provides comprehensive incident response procedures for Retell AI voice agent outages. It covers rapid triage and severity classification, immediate mitigation steps, stakeholder communication templates, evidence collection for root cause analysis, and postmortem procedures for learning and prevention.

### Technical Success Criteria

- Issue identified and severity classified
- Mitigation applied based on runbook
- Stakeholders notified via template
- Evidence collected for analysis
- Postmortem completed with action items

### Business Success Criteria

- Reduced MTTR for voice agent incidents
- Consistent incident response quality
- <15 minute MTTR for P1 Retell AI incidents

## Related Skills

- retellai-observability - Incident detection
- retellai-debug-bundle - Diagnostic collection
- retellai-advanced-troubleshooting - Deep investigation
