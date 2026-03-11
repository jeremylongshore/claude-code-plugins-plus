---
name: customerio-core-feature
description: |
  Implement Customer.io core feature integration.
  Use when implementing segments, transactional messages,
  data pipelines, or broadcast campaigns.
  Trigger with phrases like "customer.io segments", "customer.io transactional",
  "customer.io broadcast", "customer.io data pipeline".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Customer.io Core Feature Integration

## Overview
Implement Customer.io core features: segments, transactional messaging, data pipelines, and broadcast campaigns.

## Prerequisites
- Customer.io SDK configured
- Understanding of customer data model
- App API credentials for transactional emails

## Instructions

### Feature 1: Transactional Messages
### Feature 2: Segments
### Feature 3: Anonymous Tracking
### Feature 4: Object Tracking (Companies/Accounts)
### Feature 5: Data Pipeline Integration

1. For detailed implementation code and configurations, load the reference guide:
2. `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Transactional email sending capability
- Segment-ready user attributes
- Anonymous to known user merging
- B2B object tracking (companies)
- CDP data pipeline integration

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid template | Wrong message ID | Verify transactional_message_id in dashboard |
| Missing required data | Template variables missing | Check message_data contains all variables |
| Segment not updating | Attribute not matching | Verify attribute types and operators |

## Resources
- [Transactional API](https://customer.io/docs/transactional-api/)
- [Segments](https://customer.io/docs/segments/)
- [Anonymous Events](https://customer.io/docs/anonymous-events/)

## Next Steps
After implementing core features, proceed to `customerio-common-errors` to learn troubleshooting.

## Examples

**Basic usage**: Apply customerio core feature to a standard project setup with default configuration options.

**Advanced scenario**: Customize customerio core feature for production environments with multiple constraints and team-specific requirements.