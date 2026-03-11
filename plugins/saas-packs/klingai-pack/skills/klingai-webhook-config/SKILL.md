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

```
Kling AI Webhook Events:

video.created      - Job submitted, processing started
video.processing   - Generation in progress (progress updates)
video.completed    - Video generation successful
video.failed       - Generation failed with error
video.cancelled    - Job was cancelled

Payload Structure:
{
  "event": "video.completed",
  "timestamp": "2025-01-15T10:30:00Z",
  "data": {

## Detailed Reference

See `${CLAUDE_SKILL_DIR}/references/implementation.md` for complete webhook setup guide.
