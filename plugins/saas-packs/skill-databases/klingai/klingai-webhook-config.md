# klingai-webhook-config

> Configure webhooks for Kling AI job completion notifications

## Directory Structure

```
klingai-webhook-config/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 webhook_server.py       # Flask/FastAPI webhook receiver
    ├── 🐍 signature_verify.py     # Webhook signature verification
    └── 🐍 webhook_handler.py      # Event processing logic
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with webhook configuration guide |
| `webhook_server.py` | 🐍 Python | HTTP server for receiving webhooks |
| `signature_verify.py` | 🐍 Python | Verify webhook authenticity |
| `webhook_handler.py` | 🐍 Python | Process webhook events |

## Summary

**Category:** cicd
**Target Audience:** Developer building event-driven systems
**Trigger Phrases:** `klingai webhook`, `kling ai callback`, `klingai notifications`, `event-driven klingai`

### What This Skill Does

This skill configures webhooks for real-time Kling AI job notifications. It covers:

- Webhook endpoint setup and registration
- HTTPS requirements and SSL configuration
- Signature verification for security
- Event types and payload structure
- Retry handling and idempotency
- Integration with message queues

### Technical Success Criteria

- Working webhook receiving real-time notifications
- Signature verification implemented
- Idempotent event processing

### Business Success Criteria

- Efficient event-driven video processing
- Eliminated polling overhead
- Real-time status updates to users

## Related Skills

- `klingai-async-workflows` - Webhook-triggered workflows
- `klingai-batch-processing` - Batch completion notifications
- `klingai-job-monitoring` - Webhook-based monitoring
