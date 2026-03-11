---
name: klingai-webhook-config
description: |
  Configure webhooks for Kling AI job completion notifications. Use when building event-driven video
  pipelines or need real-time job status updates. Trigger with phrases like 'klingai webhook',
  'kling ai callback', 'klingai notifications', 'video completion webhook'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Kling AI Webhook Configuration

## Overview

This skill shows how to configure webhook endpoints to receive real-time notifications when video generation jobs complete, fail, or change status in Kling AI.

## Prerequisites

- Kling AI API key configured
- Public HTTPS endpoint for webhook receiver
- Python 3.8+ or Node.js 18+

## Instructions

Follow these steps to configure webhooks:

1. **Create Endpoint**: Set up a webhook receiver endpoint
2. **Register Webhook**: Configure webhook URL with Kling AI
3. **Verify Signatures**: Validate webhook authenticity
4. **Handle Events**: Process different event types
5. **Implement Retries**: Handle delivery failures

## Webhook Event Types

| Event | Description |
|-------|-------------|
| `job.completed` | Video generation finished successfully |
| `job.failed` | Video generation encountered an error |
| `job.status_changed` | Job status transitioned to a new state |

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [CI/CD implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with CI/CD |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply klingai webhook config to a standard project setup with default configuration options.

**Advanced scenario**: Customize klingai webhook config for production environments with multiple constraints and team-specific requirements.

## Resources

- Official CI/CD documentation
- Community best practices and patterns
- Related skills in this plugin pack
