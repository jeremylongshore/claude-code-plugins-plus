# retellai-phone-integration

> Configure Retell AI phone number integration for inbound and outbound calling capabilities

## Directory Structure

```
retellai-phone-integration/
├── SKILL.md
└── examples/
    └── example.py
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| SKILL.md | Markdown | Core skill instructions for phone number provisioning and call routing |
| examples/example.py | Python | Example showing phone number setup and call initiation |

## Summary

**Category:** onboarding
**Target Audience:** Voice AI developers, Telephony engineers, DevOps engineers
**Trigger Phrases:** `retell phone number`, `retell telephony`, `retell inbound calls`, `retell outbound calls`

### What This Skill Does

This skill configures Retell AI's telephony integration for production call handling. It covers provisioning phone numbers through Retell's dashboard or API, configuring inbound call routing to specific agents, setting up outbound calling capabilities for proactive engagement, and testing the full call flow from dial to conversation.

### Technical Success Criteria

- Phone number provisioned and active
- Inbound call routing configured to correct agent
- Outbound calling enabled with proper caller ID
- Test call completed successfully

### Business Success Criteria

- Revenue-generating voice channel established
- Reduced support costs through automation
- Complete phone integration with test call within 1 hour

## Related Skills

- retellai-agent-creation - Creating agents to handle calls
- retellai-call-handling - Managing call lifecycle
- retellai-webhook-server - Receiving call events
