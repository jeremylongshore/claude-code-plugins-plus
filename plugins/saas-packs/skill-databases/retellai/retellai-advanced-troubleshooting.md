# retellai-advanced-troubleshooting

> Apply advanced debugging for hard-to-diagnose issues including audio quality, latency, and transcription accuracy

## Directory Structure

```
retellai-advanced-troubleshooting/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for advanced troubleshooting techniques |
| examples/example.py | Python | Example diagnostic scripts for deep investigation |

## Summary

**Category:** advanced
**Target Audience:** Senior SREs, Staff engineers, Support escalation engineers
**Trigger Phrases:** `retell hard bug`, `retell mystery error`, `retell audio issues`, `difficult retell issue`

### What This Skill Does

This skill provides advanced troubleshooting techniques for difficult Retell AI issues. It covers audio quality analysis using FFprobe and spectrum analysis, latency profiling across the voice pipeline, transcription accuracy investigation, WebSocket connection debugging, and creating minimal reproductions for support escalation.

### Technical Success Criteria

- Comprehensive debug bundle created
- Failure layer identified (audio, STT, LLM, TTS, network)
- Minimal reproduction created
- Support escalation submitted with full context
- Resolution path identified

### Business Success Criteria

- Resolved edge-case issues that block production
- Improved system understanding
- Successfully diagnose 95% of escalated issues

## Related Skills

- retellai-debug-bundle - Initial diagnostic collection
- retellai-incident-runbook - Incident response procedures
- retellai-realtime-streaming - WebSocket debugging
