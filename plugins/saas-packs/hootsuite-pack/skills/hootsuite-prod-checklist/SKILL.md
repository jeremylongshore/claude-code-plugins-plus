---
name: hootsuite-prod-checklist
description: |
  Execute Hootsuite production deployment checklist and rollback procedures.
  Use when deploying Hootsuite integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "hootsuite production", "deploy hootsuite",
  "hootsuite go-live", "hootsuite launch checklist".
allowed-tools: Read, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite Production Checklist

## Checklist

### Authentication
- [ ] OAuth app reviewed and approved in Hootsuite developer portal
- [ ] Client secret in secrets vault
- [ ] Token refresh logic tested with expired tokens
- [ ] Separate OAuth app for production vs development

### Publishing
- [ ] Message scheduling tested with all connected social profiles
- [ ] Media upload tested (images and video if applicable)
- [ ] Error handling for REJECTED media states
- [ ] Timezone handling verified for scheduled posts
- [ ] Character limits enforced per platform (Twitter 280, LinkedIn 3000, etc.)

### Monitoring
- [ ] Token refresh failures trigger alerts
- [ ] Rate limit 429 responses logged
- [ ] Failed post scheduling reported
- [ ] Social profile disconnection detected

### Compliance
- [ ] Social media posting policies documented
- [ ] No profanity/banned words in automated posts
- [ ] Image content moderation if user-generated
- [ ] Data retention policy for scheduled posts

## Resources

- [Hootsuite Developer Portal](https://developer.hootsuite.com)
- [API Overview](https://developer.hootsuite.com/docs/api-overview)

## Next Steps

For version upgrades, see `hootsuite-upgrade-migration`.
