# retellai-voice-selection

> Select and configure AI voices from Retell AI voice library including ElevenLabs and PlayHT integrations

## Directory Structure

```
retellai-voice-selection/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for voice selection and configuration |
| examples/example.py | Python | Example showing voice listing, preview, and agent assignment |

## Summary

**Category:** onboarding
**Target Audience:** Voice AI developers, UX designers, Brand managers
**Trigger Phrases:** `retell voice`, `select retell voice`, `retell voice options`, `configure voice retell`

### What This Skill Does

This skill helps developers navigate Retell AI's extensive voice library to find the perfect voice for their use case. It covers browsing available voices from providers like ElevenLabs and PlayHT, understanding voice characteristics (accent, gender, tone), previewing voices before selection, and integrating custom voices if using voice cloning.

### Technical Success Criteria

- Voice selected from appropriate provider (11Labs, PlayHT, etc.)
- Voice configured with correct accent and speaking style
- Voice assigned to agent successfully
- Voice preview tested and approved

### Business Success Criteria

- Brand-aligned voice experience for customers
- Improved user engagement through voice matching
- Select optimal voice for use case within 15 minutes

## Related Skills

- retellai-agent-creation - Applying voice to agents
- retellai-custom-llm - Custom voice and model combinations
- retellai-conversation-design - Voice personality alignment
